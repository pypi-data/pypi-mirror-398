import subprocess as sp, os, shutil, py7zr, asyncio, json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from consoleplay import process_frame
manifest={}

async def rm(temp):
    files = [os.path.join(temp, filename) for filename in os.listdir(temp)]
    if files:
        with tqdm(total=len(files), unit='file', desc="删除文件", colour="green") as pbar:
            for file_path in files:
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    pbar.update(1)
                except Exception as e:
                    print(f'无法删除{file_path} {e}')

async def compress_directory(directory_path, output_path):
    # 修正后的文件计数逻辑，排除 process.json
    total_files = sum(
        len([f for f in files if f != "process.json"]) 
        for _, _, files in os.walk(directory_path)
    )
    
    with py7zr.SevenZipFile(output_path, 'w', mp=True) as archive:
        with tqdm(total=total_files, unit='file', desc="压缩文件",colour="green") as pbar:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file == "process.json":  # 跳过 process.json
                        continue
                    file_path = os.path.join(root, file)
                    archive.write(file_path, os.path.relpath(file_path, directory_path))
                    pbar.update(1)
async def ffmpeg_processer(input,temp,height,fps,mode) -> bool:
    ffmpeg=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/console_player_tools/ffmpeg.exe"
    if not os.path.exists(ffmpeg) or os.name=="posix":
        ffmpeg="ffmpeg"

    os.makedirs(os.path.join(temp,"frames"),exist_ok=True)
    ffmpeg_frame = [
        ffmpeg,
        '-i', input,
        '-vf', f'scale=-1:{height},fps={fps}',
        '-hide_banner',
        f'{temp}/frames/%d.jpg'
    ]
    if mode=="dp":
        ffmpeg_audio = [
            ffmpeg,
            '-i', input,
            '-vn',
            '-hide_banner',
            f'{temp}/audio.ogg'
        ]
    else:
        ffmpeg_audio = [
            ffmpeg,
            '-i', input,
            '-vn',
            '-hide_banner',
            f'{temp}/audio.mp3' 
        ]
    audio_runner=sp.run(ffmpeg_audio) # 如果你在这里报错，请安装ffmpeg并放在path里
    if audio_runner.returncode!=0:
        return False
    frame_runner=sp.run(ffmpeg_frame)
    if frame_runner.returncode!=0:
        return False
    return True

async def write_manifest(temp,mode,height,fps,xz):
    global manifest
    print("写信息文件...")
    with open(os.path.join(temp,"manifest.json"),"w") as f:
        manifest={
            "frames":len(os.listdir(os.path.join(temp,"frames"))),
            "fps":fps, 
            "type":mode,
            "xz":xz
        }
        if mode=="cpvt":
            manifest["height"]=height
        json.dump(manifest,f)
        f.close()

async def pre_gen_frames(mode,max_workers,manifest,temp,height,xz,process_json,file_count=1):
    if mode=="dp":
        pass
        #os.makedirs(os.path.join(temp,"datapack","data"),exist_ok=True)
    elif mode=="cpvt":
        frames = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            with tqdm(total=manifest["frames"], unit='frame', desc="将帧转为终端文字", colour="green") as pbar:
                # 修改路径生成方式，使用os.path处理路径
                frame_paths = [os.path.join(temp, "frames", f"{i}.jpg") for i in range(file_count, manifest["frames"] + 1)]
                if file_count!=1:
                    print("从倒下的地方再站起来！已处理的帧数量:",file_count)
                    pbar.update(file_count)
                    file_index=file_count
                else:
                    file_index=1

                
                # 分批处理帧数据，每批50个任务
                chunk_size = 50
                futures = []
                for i, path in enumerate(frame_paths):
                    futures.append(executor.submit(process_frame, path, th=height, xz=xz))
                    # 每积累一定数量的任务就等待完成
                    if (i + 1) % chunk_size == 0:
                        for future, frame_path in zip(futures, frame_paths[i-chunk_size+1:i+1]):
                            result = future.result()
                            if xz:
                                txt_path = os.path.splitext(frame_path)[0] + ".txt.xz"
                                with open(txt_path, "wb") as f:
                                    f.write(result)
                                    f.close()
                            else:
                                txt_path = os.path.splitext(frame_path)[0] + ".txt"
                                with open(txt_path, "w", encoding="utf-8") as f:
                                    f.write(result)
                                    f.close()
                            os.unlink(frame_path)

                            file_index+=1
                            pbar.update(1)

                            #with open(process_json,"r+",encoding="utf-8") as f:
                            #    process_json2=json.load(f)
                            #    process_json2["step3_processCount"]=file_index
                            #    f.seek(0)
                            #    json.dump(process_json2,f,indent=4,ensure_ascii=False)
                            #    f.truncate()
                            #    f.close()
                        futures = []
                        await asyncio.sleep(0)  # 释放事件循环
                
                # 处理剩余任务
                for future, frame_path in zip(futures, frame_paths[-len(futures):]):
                    result = future.result()
                    txt_path = os.path.splitext(frame_path)[0] + ".txt"
                    if xz:
                        txt_path = os.path.splitext(frame_path)[0] + ".txt.xz"
                        with open(txt_path, "wb") as f:
                            f.write(result)
                            f.close()
                    else:
                        txt_path = os.path.splitext(frame_path)[0] + ".txt"
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(result)
                            f.close()
                    os.unlink(frame_path)
                    pbar.update(1)
                    
                    # 先递增索引再保存进度
                    file_index += 1  # 移动到前面
                    # 使用更安全的写入方式
                    #with open(process_json, "r+", encoding="utf-8") as f:
                    #    process_data = json.load(f)
                    #    process_data["step3_processCount"] = file_index
                    #    f.seek(0)
                    #    json.dump(process_data, f, indent=4, ensure_ascii=False)
                    #    f.truncate()
    await asyncio.sleep(0.5)

async def gen(input,output,mode,height,fps,temp,max_workers=None,xz=False):
    global manifest
    # 初始化部分
    if not os.path.exists(os.path.join(temp,"process.json")):
        await rm(temp)
        start_i=0
        step3_processCount=1
        process_json={
            "step":0,
            "step3_processCount":1,
            "argments": {
                "input":input,
                "output":output,
                "mode":mode,
                "height":height,
                "fps":fps,
                "temp":temp,
                "max_workers":max_workers,
                "xz":xz
            }
        }
    else:
        with open(os.path.join(temp,"process.json"),"r",encoding="utf-8") as f:
            process_json=json.load(f)
            start_i=process_json["step"]
            step3_processCount=process_json["step3_processCount"]
            f.close()
        if start_i>=2:
            with open(os.path.join(temp,"manifest.json"),"r") as f:
                print("读回manifest...")
                manifest=json.load(f)
                f.close()

    for i in range(start_i,5):
        if i==0:
            await ffmpeg_processer(input,temp,height,fps,mode)
        elif i==1:
            await write_manifest(temp,mode,height,fps,xz)
        elif i==2:
            await pre_gen_frames(mode,max_workers,manifest,temp,height,xz,os.path.join(temp,"process.json"),step3_processCount)
        elif i==3:
            await compress_directory(temp,output)
        elif i==4:
            print("再次清空目录...")
            await rm(temp)
            await asyncio.sleep(0.5)
            break
        with open(os.path.join(temp,"process.json"),"w",encoding="utf-8") as f:
            process_json["step"]=i
            f.close()
            