import os
import sys
import tempfile
from mxboxutils.file import files, file_paths, imgs, img_paths, file_hash
from mxboxutils.toml import load_toml


def test_files():
    """测试 files 函数的功能"""
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        for i in range(3):
            with open(os.path.join(temp_dir, f"test{i}.txt"), "w") as f:
                f.write("test content")
        for i in range(2):
            with open(os.path.join(temp_dir, f"test{i}.jpg"), "w") as f:
                f.write("image content")
        
        # 测试 files 函数
        txt_files = files(temp_dir, ["txt"])
        assert len(txt_files) == 3
        assert all(f.endswith(".txt") for f in txt_files)
        
        print("✓ files 函数测试通过")


def test_file_paths():
    """测试 file_paths 函数的功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        for i in range(2):
            with open(os.path.join(temp_dir, f"test{i}.py"), "w") as f:
                f.write("python code")
        
        # 测试 file_paths 函数
        py_paths = file_paths(temp_dir, ["py"])
        assert len(py_paths) == 2
        assert all(os.path.exists(path) for path in py_paths)
        assert all(path.endswith(".py") for path in py_paths)
        
        print("✓ file_paths 函数测试通过")


def test_imgs():
    """测试 imgs 函数的功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试图像文件
        for i in range(2):
            with open(os.path.join(temp_dir, f"image{i}.jpg"), "w") as f:
                f.write("image data")
        with open(os.path.join(temp_dir, "document.pdf"), "w") as f:
            f.write("pdf content")
        
        # 测试 imgs 函数
        image_files = imgs(temp_dir)
        assert len(image_files) == 2
        assert all(f.endswith(".jpg") for f in image_files)
        
        print("✓ imgs 函数测试通过")


def test_img_paths():
    """测试 img_paths 函数的功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试图像文件
        for i in range(3):
            with open(os.path.join(temp_dir, f"img{i}.png"), "w") as f:
                f.write("png data")
        
        # 测试 img_paths 函数
        image_paths = img_paths(temp_dir)
        assert len(image_paths) == 3
        assert all(os.path.exists(path) for path in image_paths)
        assert all(path.endswith(".png") for path in image_paths)
        
        print("✓ img_paths 函数测试通过")


def test_file_hash():
    """测试 file_hash 函数的功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test hash")
        
        # 测试 SHA256
        sha256_hash = file_hash(test_file, "SHA256")
        assert sha256_hash != "Invalid File"
        assert sha256_hash != "Invalid Hash Type"
        assert sha256_hash != "No Hash Code"
        
        # 测试 MD5
        md5_hash = file_hash(test_file, "MD5")
        assert md5_hash != "Invalid File"
        assert md5_hash != "Invalid Hash Type"
        assert md5_hash != "No Hash Code"
        
        # 测试无效哈希类型
        invalid_hash = file_hash(test_file, "INVALID")
        assert invalid_hash == "Invalid Hash Type"
        
        # 测试无效文件
        invalid_file_hash = file_hash("/invalid/path.txt", "SHA256")
        assert invalid_file_hash == "Invalid File"
        
        print("✓ file_hash 函数测试通过")


def test_load_toml():
    """测试 load_toml 函数的功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.toml")
        
        # 创建测试 TOML 文件
        with open(test_file, "w") as f:
            f.write("""[test]
key = "value"
number = 42
""")
        
        # 测试加载 TOML 文件
        data = load_toml(test_file)
        assert data is not None
        assert "test" in data
        assert data["test"]["key"] == "value"
        assert data["test"]["number"] == 42
        
        # 测试加载不存在的文件
        non_existent_data = load_toml("/invalid/path.toml")
        assert non_existent_data is None
        
        print("✓ load_toml 函数测试通过")


if __name__ == "__main__":
    print("Running tests for MxBoxUtils...")
    print()
    
    test_files()
    test_file_paths()
    test_imgs()
    test_img_paths()
    test_file_hash()
    test_load_toml()
    
    print()
    print("🎉 All tests passed!")