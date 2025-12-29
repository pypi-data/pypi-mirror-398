class Msg:
    OK = "Thành công"
    CREATED = "Tạo mới thành công"
    NO_CONTENT = "Không có dữ liệu"

    BAD_REQUEST = "Yêu cầu không hợp lệ"
    UNAUTHORIZED = "Chưa cung cấp thông tin xác thực."
    FORBIDDEN = "Bạn không có quyền thực hiện hành động này."
    NOT_FOUND = "Không tìm thấy dữ liệu."
    CONFLICT = "Xung đột dữ liệu"
    TOO_MANY_REQUESTS = "Quá nhiều yêu cầu, vui lòng thử lại sau"

    INTERNAL_SERVER_ERROR = "Hệ thống gặp lỗi, vui lòng thử lại sau"
    BAD_GATEWAY = "Hệ thống đang bận kết nối, vui lòng chờ và thử lại"

    VALUE_INVALID = "Dữ liệu không hợp lệ"
    GET_ERROR = "Không thể lấy dữ liệu"
    DELETED_ERROR = "Không thể xoá dữ liệu"
    CREATED_ERROR = "Không thể tạo dữ liệu"
    UPDATED_ERROR = "Không thể cập nhật dữ liệu"
    GET_DETAIL_ERROR = "Không thể lấy chi tiết dữ liệu"

    INVALID_TOKEN = "Token không hợp lệ."
    USER_INACTIVE = "Người dùng đã bị vô hiệu hoá hoặc đã bị xoá."
    AUTH_FAILED = "Xác thực thất bại."
    INVALID_USERNAME_PASSWORD = "Tên đăng nhập hoặc mật khẩu không đúng."
    INVALID_BASIC_HEADER = "Header Basic không hợp lệ. Chưa cung cấp thông tin xác thực."
    INVALID_BASIC_HEADER_SPACES = "Header Basic không hợp lệ. Chuỗi xác thực không được chứa khoảng trắng."
    INVALID_BASIC_HEADER_BASE64 = "Header Basic không hợp lệ. Chuỗi xác thực không được mã hoá base64 đúng."
    INVALID_TOKEN_HEADER = "Header Token không hợp lệ. Chưa cung cấp token."
    INVALID_TOKEN_HEADER_CHAR = "Header Token không hợp lệ. Token chứa ký tự không hợp lệ."

    METHOD_NOT_ALLOWED = 'Phương thức "%s" không được phép.'
    UNSUPPORTED_MEDIA_TYPE = 'Kiểu dữ liệu "%s" không được hỗ trợ.'
    INVALID_PAGE = "Trang không hợp lệ."
    CSRF_FAILED = "CSRF thất bại: Thiếu hoặc sai CSRF token."

    FIELD_REQUIRED = "Trường này là bắt buộc."
    FIELD_NULL = "Trường này không được để null."
    FIELD_BLANK = "Trường này không được để trống."
    FIELD_INVALID = "Giá trị không hợp lệ."
    LIST_EMPTY = "Danh sách không được để trống."
    LIST_MAX_ITEMS = "Danh sách không được chứa quá %(max_length)d phần tử."
    LIST_MIN_ITEMS = "Danh sách phải chứa ít nhất %(min_length)d phần tử."
    EMAIL_INVALID = "Email không hợp lệ."
    URL_INVALID = "URL không hợp lệ."
    INTEGER_INVALID = "Vui lòng nhập số nguyên hợp lệ."
    NUMBER_INVALID = "Vui lòng nhập số hợp lệ."
    MAX_LENGTH = "Giá trị tối đa %(limit_value)d ký tự (hiện tại %(show_value)d)."
    MIN_LENGTH = "Giá trị tối thiểu %(limit_value)d ký tự (hiện tại %(show_value)d)."
    MIN_VALUE = "Giá trị phải lớn hơn hoặc bằng %(limit_value)s."
    MAX_VALUE = "Giá trị phải nhỏ hơn hoặc bằng %(limit_value)s."

    PASSWORD_TOO_SHORT = "Mật khẩu quá ngắn. Tối thiểu %(min_length)d ký tự."
    PASSWORD_TOO_COMMON = "Mật khẩu quá phổ biến."
    PASSWORD_NUMERIC = "Mật khẩu không được chỉ chứa số."
    DATE_INVALID = "Ngày không hợp lệ."
    TIME_INVALID = "Thời gian không hợp lệ."
    DATETIME_INVALID = "Ngày giờ không hợp lệ."
    IPV4_INVALID = "Địa chỉ IPv4 không hợp lệ."
    IPV6_INVALID = "Địa chỉ IPv6 không hợp lệ."
    UUID_INVALID = "UUID không hợp lệ."

    CONSTRAINT_VIOLATED = 'Ràng buộc "%(name)s" bị vi phạm.'
    NULL_NOT_ALLOWED = "Trường này không được để null."
    CANNOT_BE_BLANK = "Trường này không được để trống."
    CANNOT_BE_EMPTY = "Trường này không được để rỗng."

    THIS_VALUE_ALREADY_EXISTS = "Giá trị này đã tồn tại."
    OBJECT_WITH_VALUE_ALREADY_EXISTS = "%(model)s với %(field)s này đã tồn tại."
    DUPLICATE_VALUE = "Giá trị bị trùng lặp."
    VALUE_MUST_BE_UNIQUE = "Giá trị phải là duy nhất."
    UNIQUE_CONSTRAINT_ERROR = "Vi phạm ràng buộc duy nhất."
    INTEGRITY_ERROR = "Lỗi toàn vẹn dữ liệu."

    UNIQUE_CONSTRAINT_VIOLATION = "Dữ liệu gửi lên không duy nhất."
    FOREIGN_KEY_CONSTRAINT_VIOLATION = "Tham chiếu không hợp lệ: %(obj)s.%(field)s"
    CHECK_CONSTRAINT_VIOLATION = "Ràng buộc kiểm tra (%(check)s) bị vi phạm."

    INVALID_CHOICE = '"%(value)s" không phải là lựa chọn hợp lệ. Các lựa chọn hợp lệ: %(choices_text)s.'
    INVALID_PRIMARY_KEY = 'Giá trị "%(pk)s" không đúng định dạng. Phải là số.'
    MISSING_FIELDS = "Thiếu các trường: %(missing_fields)s"
    NON_FIELD_ERRORS = "Lỗi không xác định tại trường '%(field)s'."

    VALUE_TOO_LONG = "Chuỗi quá dài: tối đa %(max_length)d ký tự, hiện tại %(value_length)d."
    VALUE_TOO_SHORT = "Chuỗi quá ngắn: tối thiểu %(min_length)d ký tự, hiện tại %(value_length)d."

    EXCEEDED_MAX_DIGITS = "Không được vượt quá %(max)s chữ số."
    EXCEEDED_DECIMAL_PLACES = "Không được vượt quá %(max)s chữ số thập phân."
    MAX_DIGITS_EXCEEDED = "Số chữ số vượt quá giới hạn %(max)s."
    DECIMAL_PLACES_EXCEEDED = "Số chữ số thập phân vượt quá %(max)s."

    INVALID_IMAGE = "Vui lòng tải lên hình ảnh hợp lệ. Tệp có thể không phải hình ảnh hoặc đã bị hỏng."
    EMPTY_FILE = "Tệp tải lên rỗng."
    FILE_TOO_LARGE = "Dung lượng tệp không được vượt quá %(size)d.%(size_type)s. Dung lượng hiện tại: %(file_size)d.%(size_type)s."
    FILE_EXTENSION_INVALID = "Định dạng tệp '%(extension)s' không được phép. Các định dạng cho phép: %(allowed_extensions)s."

    INVALID_DATE_FORMAT = "Định dạng ngày không hợp lệ. Định dạng đúng: %(format)s"
    INVALID_TIME_FORMAT = "Định dạng thời gian không hợp lệ. Định dạng đúng: %(format)s"
    INVALID_DATETIME_FORMAT = "Định dạng ngày giờ không hợp lệ. Định dạng đúng: %(format)s"
    DATE_IN_PAST = "Ngày không được nằm trong quá khứ."
    DATE_IN_FUTURE = "Ngày không được nằm trong tương lai."

    CANNOT_DELETE_PROTECTED_OBJECT = "Không thể xoá %(object)s vì đang được tham chiếu bởi %(referenced_objects)s."
    INVALID_FOREIGN_KEY_REFERENCE = "Giá trị tham chiếu không hợp lệ."
    RELATED_OBJECT_DOES_NOT_EXIST = "Đối tượng liên kết %(relation)s không tồn tại."

    INVALID_ARRAY_DATA = "Dữ liệu JSON không hợp lệ."
    INVALID_ARRAY_DECODER = "Không thể giải mã JSON."
    OUT_OF_MEMORY_DURING_ARRAY_CONSTRUCTION = "Không đủ bộ nhớ khi xử lý mảng."
    INVALID_ARRAY_DIMENSIONS = "Kích thước mảng không hợp lệ."

    INVALID_JSON = "Giá trị phải là JSON hợp lệ."
    CANNOT_SET_JSON_NULL = "Không thể gán null cho JSONField khi null=False."
    MUST_BE_JSON_ONLY = "Chỉ chấp nhận dữ liệu JSON."

    MODEL_VALIDATION_ERROR = "Lỗi kiểm tra model: %(error)s"
    FIELD_VALIDATION_ERROR = "Lỗi kiểm tra trường '%(field)s': %(error)s"
    UNKNOWN_ERROR = "Đã xảy ra lỗi không xác định"
    VALIDATION_ERROR = "Đã xảy ra lỗi xác thực dữ liệu"
    SHOW_COUNTS = "Hiển thị số lượng"
