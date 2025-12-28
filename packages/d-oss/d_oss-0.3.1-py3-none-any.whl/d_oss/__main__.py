from typing import Literal, Optional
import zipfile
import os
from pathlib import Path
from datetime import datetime

import oss2
from oss2 import Bucket
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from jsonargparse import auto_cli, set_parsing_settings
import srsly

set_parsing_settings(parse_optionals_as_positionals=True)

console = Console()


def get_dir_info(dir_path):
    """获取目录的总大小和文件数"""
    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except (OSError, IOError):
                    # 跳过无法访问的文件
                    pass
    except (OSError, IOError):
        pass
    return total_size, file_count


def zip_all_files(dir, zipFile, pre_dir, progress_callback=None):
    """递归压缩文件夹下的所有文件
    参数:
    - dir: 要压缩的文件夹路径
    - zipFile: zipfile对象
    - pre_dir: 压缩文件根目录
    - progress_callback: 进度回调函数，参数为(current_size, total_size)
    """
    for f in os.listdir(dir):
        absFile = os.path.join(dir, f)  # 子文件的绝对路径
        pre_d = os.path.join(pre_dir, f)
        if os.path.isdir(absFile):  # 判断是文件夹，继续深度读取。
            zipFile.write(absFile, pre_d)  # 在zip文件中创建文件夹
            zip_all_files(
                absFile, zipFile, pre_dir=pre_d, progress_callback=progress_callback
            )
        else:  # 判断是普通文件，直接写到zip文件中。
            file_size = os.path.getsize(absFile)
            zipFile.write(absFile, pre_d)
            if progress_callback:
                # 传递当前文件大小的增量
                progress_callback(file_size, 0)  # 第二个参数0表示这是增量大小


def save_auth(auth_file: Path, access_key_id: str, access_key_secret: str):
    if not auth_file.exists():
        auth_file.parent.mkdir(parents=True, exist_ok=True)
    srsly.write_json(
        auth_file,
        {"access_key_id": access_key_id, "access_key_secret": access_key_secret},
    )


def load_auth(auth_file: Path):
    if not auth_file.exists():
        access_key_id = None
        access_key_secret = None
    else:
        auth = srsly.read_json(auth_file)
        access_key_id = auth.get("access_key_id", None)
        access_key_secret = auth.get("access_key_secret", None)
    if access_key_id is None or access_key_secret is None:
        access_key_id = console.input("access_key_id: ")
        if access_key_id == "":
            raise ValueError("access_key_id cannot be empty")
        access_key_secret = console.input("access_key_secret: ")
        if access_key_secret == "":
            raise ValueError("access_key_secret cannot be empty")
        save_auth(auth_file, access_key_id, access_key_secret)
    return access_key_id, access_key_secret


class OSSStorer:
    """阿里云oss对象存储"""

    def __init__(
        self,
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        cache_dir: str | Path = Path().home() / ".cache" / "d-oss",
    ):
        super().__init__()
        self.auth_file = Path(cache_dir) / "auth.json"
        access_key_id, access_key_secret = load_auth(self.auth_file)
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        beijing_endpoint: str = "http://oss-cn-beijing.aliyuncs.com"
        hangzhou_endpoint: str = "http://oss-cn-hangzhou.aliyuncs.com"
        data_bucket: str = "deepset"
        model_bucket: str = "pretrained-model"
        asset_bucket: str = "deepasset"
        corpus_bucket: str = "deepcorpus"
        pipe_bucket: str = "spacy-pipeline"
        self.data_bucket = oss2.Bucket(
            self.auth, beijing_endpoint, bucket_name=data_bucket
        )
        self.model_bucket = oss2.Bucket(
            self.auth, beijing_endpoint, bucket_name=model_bucket
        )
        self.assets_bucket = oss2.Bucket(
            self.auth, beijing_endpoint, bucket_name=asset_bucket
        )
        self.corpus_bucket = oss2.Bucket(
            self.auth, hangzhou_endpoint, bucket_name=corpus_bucket
        )
        self.pipe_bucket = oss2.Bucket(
            self.auth, beijing_endpoint, bucket_name=pipe_bucket
        )

        self.buckets = {
            "data": self.data_bucket,
            "model": self.model_bucket,
            "asset": self.assets_bucket,
            "corpus": self.corpus_bucket,
            "pipeline": self.pipe_bucket,
        }

        self.cache_dir = cache_dir

    def list(
        self,
        bucket: Optional[
            Literal["data", "model", "asset", "corpus", "pipeline"]
        ] = None,
    ) -> None:
        """获取bucket下的所有文件

        Args:
            bucket: 要列出的bucket名称，如果不指定则显示所有bucket的内容
        """
        # 验证bucket参数
        valid_buckets = ["data", "model", "asset", "corpus", "pipeline"]
        if bucket is not None and bucket not in valid_buckets:
            console.print(
                f"[bold red]错误：无效的bucket名称 '{bucket}'，有效选项：{', '.join(valid_buckets)}[/bold red]"
            )
            return

        if bucket is None:
            # 显示所有bucket的内容
            bucket_names = list(self.buckets.keys())

            for bucket_name in bucket_names:
                bucket_obj = self.buckets[bucket_name]

                # 获取bucket中的文件列表
                objects = list(oss2.ObjectIterator(bucket_obj))
                file_count = len(objects)

                # 显示bucket标题和文件数量
                console.print(
                    f"\n[bold cyan]📁 Bucket: {bucket_name} ({file_count} files)[/bold cyan]"
                )

                if file_count == 0:
                    console.print("  [dim](empty)[/dim]")
                    continue

                # 创建表格显示文件
                table = Table(show_header=True, header_style="bold blue")
                table.add_column("File Name", style="cyan")
                table.add_column("Size", style="green", justify="right")
                table.add_column("Last Modified", style="yellow", justify="center")

                for obj in objects:
                    # 格式化文件大小
                    size_mb = obj.size / 1024 / 1024 if obj.size else 0
                    size_str = (
                        f"{size_mb:.2f} MB"
                        if obj.size >= 1024 * 1024
                        else f"{obj.size or 0} B"
                    )

                    # 格式化时间
                    last_modified = (
                        datetime.fromtimestamp(obj.last_modified).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if hasattr(obj, "last_modified") and obj.last_modified
                        else "Unknown"
                    )

                    table.add_row(obj.key, size_str, last_modified)

                console.print(table)

            console.print(
                f"\n[bold green]✅ Listed contents of {len(bucket_names)} buckets[/bold green]"
            )

        else:
            # 显示单个bucket的内容
            bucket_obj = self.buckets.get(bucket)

            # 获取bucket中的文件列表
            objects = list(oss2.ObjectIterator(bucket_obj))
            file_count = len(objects)

            console.print(
                f"[bold cyan]📁 Bucket: {bucket} ({file_count} files)[/bold cyan]"
            )

            if file_count == 0:
                console.print("  [dim](empty)[/dim]")
                return

            # 创建表格显示文件
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("File Name", style="cyan")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Last Modified", style="yellow", justify="center")

            for obj in objects:
                # 格式化文件大小
                size_mb = obj.size / 1024 / 1024 if obj.size else 0
                size_str = (
                    f"{size_mb:.2f} MB"
                    if obj.size >= 1024 * 1024
                    else f"{obj.size or 0} B"
                )

                # 格式化时间
                last_modified = (
                    datetime.fromtimestamp(obj.last_modified).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if hasattr(obj, "last_modified") and obj.last_modified
                    else "Unknown"
                )

                table.add_row(obj.key, size_str, last_modified)

            console.print(table)

    def upload(
        self, file: str, bucket: Literal["data", "model", "asset", "corpus", "pipeline"]
    ):
        """上传文件或者目录到bucket
        - file: 要上传的文件路径
        - bucket: 要上传到的bucket
        """
        file_path: Path = Path(file)
        if not file_path.exists():
            console.print(f"[bold red] file {file} not exists!")
            return
        bucket_obj: oss2.Bucket = self.buckets.get(bucket)

        if file_path.is_dir():
            # 目录上传：压缩 + 上传两个阶段
            file_zip_path = file_path.name + ".zip"
            total_size, file_count = get_dir_info(file_path)

            with Progress(
                TextColumn("[bold blue]{task.description}", justify="left"),
                BarColumn(bar_width=30),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("[bold green]{task.fields[size_info]}", justify="left"),
                TransferSpeedColumn(),
                TextColumn("[cyan]已用时:"),
                TimeElapsedColumn(),
                TextColumn("[yellow]剩余:"),
                TimeRemainingColumn(),
            ) as progress:
                # 压缩阶段
                zip_task = progress.add_task(
                    f"📦 compressing {file_path.name}",
                    size_info=f"0/{file_count} files • 0.0/{total_size / 1024 / 1024:.1f} MB",
                    total=total_size,
                )

                compressed_size = 0
                compressed_files = 0

                def zip_progress(size_increment, _):
                    nonlocal compressed_size, compressed_files
                    # 累加已压缩大小
                    compressed_size += size_increment
                    compressed_files += 1

                    if total_size > 0:
                        size_mb = compressed_size / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        progress.update(
                            zip_task,
                            completed=compressed_size,
                            total=total_size,
                            size_info=f"{compressed_files}/{file_count} files • {size_mb:.1f}/{total_mb:.1f} MB",
                        )
                    else:
                        size_mb = compressed_size / 1024 / 1024
                        progress.update(
                            zip_task,
                            completed=compressed_size,
                            total=compressed_size or 1,  # 避免除零错误
                            size_info=f"{compressed_files}/{file_count} files • {size_mb:.1f}/0.0 MB",
                        )

                with zipfile.ZipFile(file=file_zip_path, mode="w") as z:
                    zip_all_files(
                        file_path, z, file_path.name, progress_callback=zip_progress
                    )

                # 完成压缩任务
                progress.update(zip_task, completed=total_size)

                # 上传阶段
                zip_size = os.path.getsize(file_zip_path)
                upload_task = progress.add_task(
                    f"☁️  uploading {file_zip_path}",
                    total=zip_size,
                    size_info=f"{zip_size / 1024 / 1024:.1f} MB",
                )

                # 移除已完成的压缩任务
                progress.remove_task(zip_task)

                def upload_progress(consumed_bytes, total_bytes):
                    consumed_mb = consumed_bytes / 1024 / 1024
                    total_mb = total_bytes / 1024 / 1024
                    progress.update(
                        upload_task,
                        completed=consumed_bytes,
                        total=total_bytes,
                        size_info=f"{consumed_mb:.1f}/{total_mb:.1f} MB",
                    )

                upload_success = False
                try:
                    bucket_obj.put_object_from_file(
                        key=file_zip_path,
                        filename=file_zip_path,
                        progress_callback=upload_progress,
                    )
                    upload_success = True
                except Exception as e:
                    console.print(
                        f"[bold red]❌ upload {file_path} to {bucket} failed with error: {e}"
                    )
                except KeyboardInterrupt:
                    console.print("[yellow]⚠️  upload cancelled by user")
                finally:
                    if os.path.exists(file_zip_path):
                        os.remove(path=file_zip_path)

            if upload_success:
                console.print(f"[bold green]✅ upload {file_path} to {bucket} succeed")
        else:
            # 单个文件上传
            file_size = os.path.getsize(file_path)
            with Progress(
                TextColumn("[bold blue]{task.description}", justify="left"),
                BarColumn(bar_width=30),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TransferSpeedColumn(),
                TextColumn("[cyan]已用时:"),
                TimeElapsedColumn(),
                TextColumn("[yellow]剩余:"),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"☁️  uploading {file_path.name}", total=file_size
                )

                def upload_progress(consumed_bytes, total_bytes):
                    progress.update(task, completed=consumed_bytes, total=total_bytes)

                upload_success = False
                try:
                    bucket_obj.put_object_from_file(
                        key=file_path.name,
                        filename=file_path,
                        progress_callback=upload_progress,
                    )
                    upload_success = True
                except Exception as e:
                    console.print(
                        f"[bold red]❌ upload {file_path} to {bucket} failed with error: {e}"
                    )
                except KeyboardInterrupt:
                    console.print("[yellow]⚠️  upload cancelled by user")

            if upload_success:
                console.print(f"[bold green]✅ upload {file_path} to {bucket} succeed")

    def download(
        self,
        file: str,
        bucket: Literal["data", "model", "asset", "corpus", "pipeline"],
        save_dir: str = "./",
        force: bool = False,
    ):
        """下载数据集
        - file: 要下载的文件
        - bucket: 要下载的bucket
        - save_dir: 保存目录, 默认当前目录
        """
        if save_dir is None:
            save_dir = bucket
        save_dir: Path = Path(save_dir)
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        bucket_obj: Bucket = self.buckets.get(bucket)
        file_path = save_dir / file

        if file_path.exists() and not force:
            file_size = file_path.stat().st_size
            console.print(
                f"[yellow]⚠️  File '{file}' already exists in {save_dir} ({file_size / 1024 / 1024:.1f} MB)[/yellow]"
            )
            console.print(
                "[bold cyan]💡 Tip: Use --force to overwrite existing file[/bold cyan]"
            )
            return

        try:
            console.print(
                f"[blue]🚀 Starting download of '{file}' from bucket '{bucket}'[/blue]"
            )
            with Progress(
                TextColumn("[bold blue]{task.description}", justify="left"),
                BarColumn(bar_width=30),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("[bold green]{task.fields[size_info]}", justify="left"),
                TransferSpeedColumn(),
                TextColumn("[cyan]已用时:"),
                TimeElapsedColumn(),
                TextColumn("[yellow]剩余:"),
                TimeRemainingColumn(),
            ) as progress:
                # 下载阶段
                download_task = progress.add_task(
                    f"⬇️  downloading {file}", size_info="0.0/0.0 MB"
                )

                def download_progress(consumed_bytes, total_bytes):
                    if total_bytes > 0:
                        consumed_mb = consumed_bytes / 1024 / 1024
                        total_mb = total_bytes / 1024 / 1024
                        progress.update(
                            download_task,
                            total=total_bytes,
                            completed=consumed_bytes,
                            size_info=f"{consumed_mb:.1f}/{total_mb:.1f} MB",
                        )

                bucket_obj.get_object_to_file(
                    key=file,
                    filename=file_path,
                    progress_callback=download_progress,
                )

                # 完成下载任务
                progress.update(download_task, completed=file_path.stat().st_size)
                progress.remove_task(download_task)

                # 如果是zip文件，进行解压
                if file.endswith(".zip"):
                    with zipfile.ZipFile(file=file_path, mode="r") as zf:
                        # 获取zip文件信息
                        total_files = len(zf.namelist())
                        extracted_files = 0

                        extract_task = progress.add_task(
                            f"📦 extracting {file}", size_info=f"0/{total_files} files"
                        )

                        def extract_progress():
                            nonlocal extracted_files
                            extracted_files += 1
                            progress.update(
                                extract_task,
                                completed=extracted_files,
                                total=total_files,
                                size_info=f"{extracted_files}/{total_files} files",
                            )

                        # 逐个提取文件并更新进度
                        for member in zf.namelist():
                            zf.extract(member, path=save_dir)
                            extract_progress()

                        # 完成解压任务
                        progress.update(extract_task, completed=total_files)
                        progress.remove_task(extract_task)

                    # 删除zip文件
                    file_path.unlink()

            console.print(f"[bold green]✅ download {file} to {save_dir} succeed")
        except Exception as e:
            console.print(
                f"[bold red]❌ download {file} to {save_dir} failed with error: {e}"
            )
        except KeyboardInterrupt:
            console.print("[yellow]⚠️  download cancelled by user")
            # 清理未完成的文件
            if file_path.exists():
                file_path.unlink()

    def delete(
        self, file: str, bucket: Literal["data", "model", "asset", "corpus", "pipeline"]
    ):
        """删除文件或者目录

        Args:
            file: 要删除的文件名，或使用 "ALL" 删除bucket中的所有文件
            bucket: bucket名称

        Examples:
            # 删除单个文件
            oss delete myfile.zip model

            # 删除bucket中的所有文件
            oss delete "ALL" model
        """
        bucket_obj: Bucket = self.buckets.get(bucket)

        if file.upper() == "ALL":
            # 删除bucket中的所有文件
            console.print(
                f"[yellow]🗑️  Deleting all files from bucket '{bucket}'...[/yellow]"
            )

            deleted_count = 0
            total_size = 0

            try:
                # 获取所有对象
                objects = list(oss2.ObjectIterator(bucket_obj))

                if not objects:
                    console.print(f"[blue]📂 Bucket '{bucket}' is already empty[/blue]")
                    return

                console.print(f"[dim]Found {len(objects)} files to delete[/dim]")

                # 删除所有对象
                for obj in objects:
                    try:
                        bucket_obj.delete_object(obj.key)
                        deleted_count += 1
                        total_size += obj.size if hasattr(obj, "size") else 0

                        # 每删除10个文件显示一次进度
                        if deleted_count % 10 == 0 or deleted_count == len(objects):
                            console.print(
                                f"[dim]Deleted {deleted_count}/{len(objects)} files...[/dim]"
                            )

                    except Exception as e:
                        console.print(f"[red]❌ Failed to delete {obj.key}: {e}[/red]")

                size_mb = total_size / 1024 / 1024
                console.print(
                    f"[bold green]✅ Successfully deleted {deleted_count} files ({size_mb:.1f} MB) from bucket '{bucket}'[/bold green]"
                )

            except Exception as e:
                console.print(
                    f"[bold red]❌ Failed to delete files from bucket '{bucket}': {e}[/bold red]"
                )

        else:
            # 删除单个文件
            if bucket_obj.object_exists(file):
                try:
                    # 获取文件大小（如果可能）
                    obj_info = bucket_obj.get_object_meta(file)
                    size = obj_info.headers.get("Content-Length", "unknown")
                    if size != "unknown":
                        size_mb = int(size) / 1024 / 1024
                        size_info = f" ({size_mb:.1f} MB)"
                    else:
                        size_info = ""

                    bucket_obj.delete_object(file)
                    console.print(
                        f"[bold green]✅ Deleted '{file}'{size_info} from bucket '{bucket}'[/bold green]"
                    )
                except Exception as e:
                    console.print(
                        f"[bold red]❌ Failed to delete '{file}' from bucket '{bucket}': {e}[/bold red]"
                    )
            else:
                console.print(
                    f"[yellow]⚠️  File '{file}' does not exist in bucket '{bucket}'[/yellow]"
                )

    def clear(self):
        """清空本地缓存和API密钥"""
        if self.auth_file.exists():
            os.remove(self.auth_file)

    def info(self):
        """
        打印当前的auth信息
        """
        access_key_id, access_key_secret = load_auth(self.auth_file)
        console.print("[bold cyan]auth:[/bold cyan]")
        console.print(f"  access_key_id: {access_key_id}")
        console.print(f"  access_key_secret: {access_key_secret}")


def run():
    auto_cli(OSSStorer, as_positional=True)


if __name__ == "__main__":
    run()
