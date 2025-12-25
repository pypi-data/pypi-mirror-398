def is_vietnamese(text: str) -> bool:
    return any(
        c in text for c in "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụýỳỷỹỵ"
    )
