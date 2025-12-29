from sapiopycommons.files.file_util import FileUtil

files: dict[str, bytes] = {
    "file1.txt": b"Hello, this is the content of file 1.",
    "file2.txt": b"This is file 2, containing some sample text.",
    "file3.txt": b"File 3 is here with its own unique content.",
    "file4.txt": b"And finally, this is file 4."
}

print("files -> .zip -> files")
zip_file: bytes = FileUtil.zip_files(files)
with open("test_output/test.zip", "wb") as f:
    f.write(zip_file)
unzipped_files: dict[str, bytes] = FileUtil.unzip_files(zip_file)
for filename, content in unzipped_files.items():
    print(f"\t{filename}: {content.decode('utf-8')}")

print("file -> .gz -> file")
gz_file: bytes = FileUtil.gzip_file(files["file1.txt"])
with open("test_output/file1.txt.gz", "wb") as f:
    f.write(gz_file)
ungzipped_file: bytes = FileUtil.ungzip_file(gz_file)
print(f"\tUngzipped file1.txt: {ungzipped_file.decode('utf-8')}")

print("files -> .tar -> files")
tarfile: bytes = FileUtil.tar_files(files)
with open("test_output/test.tar", "wb") as f:
    f.write(tarfile)
untarred_files: dict[str, bytes] = FileUtil.untar_files(tarfile)
for filename, content in untarred_files.items():
    print(f"\t{filename}: {content.decode('utf-8')}")

print("files -> .tar.gz -> files")
tgz_file: bytes = FileUtil.tar_gzip_files(files)
with open("test_output/test.tar.gz", "wb") as f:
    f.write(tgz_file)
untgzipped_files: dict[str, bytes] = FileUtil.untar_gzip_files(tgz_file)
for filename, content in untgzipped_files.items():
    print(f"\t{filename}: {content.decode('utf-8')}")
