import paddle
from paddleocr import PaddleOCR

# Kiểm tra xem Paddle có nhận diện được GPU không
print(f"Hỗ trợ GPU: {paddle.device.is_compiled_with_cuda()}")

# Chạy thử khởi tạo OCR
ocr = PaddleOCR(use_angle_cls=True, lang='ru')
print("Khởi tạo PaddleOCR thành công!")
