use std::fmt;

/// Early Return Error - 携带返回值的自定义错误
///
/// 当 JavaScript 调用 __neverjscore_return__() 时,
/// 会抛出此错误来中断执行并返回值到 Rust 侧
#[derive(Debug, Clone)]
pub struct EarlyReturnError {
    /// JSON 格式的返回值
    pub value: String,
}

impl fmt::Display for EarlyReturnError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[NEVER_JSCORE_EARLY_RETURN]{}", self.value)
    }
}

impl std::error::Error for EarlyReturnError {}

impl EarlyReturnError {
    pub fn new(value: String) -> Self {
        Self { value }
    }

    /// 从错误消息中提取返回值
    /// 格式: [NEVER_JSCORE_EARLY_RETURN]<json_value>
    pub fn extract_from_message(msg: &str) -> Option<String> {
        const PREFIX: &str = "[NEVER_JSCORE_EARLY_RETURN]";
        if msg.starts_with(PREFIX) {
            Some(msg[PREFIX.len()..].to_string())
        } else {
            None
        }
    }
}
