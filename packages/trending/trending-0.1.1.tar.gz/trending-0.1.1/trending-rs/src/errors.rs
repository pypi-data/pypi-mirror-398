use std::backtrace::Backtrace;

use snafu::{Location, Snafu};

pub type Result<T> = std::result::Result<T, TrendingError>;

#[derive(Debug, Snafu)]
#[snafu(visibility(pub))]
pub enum TrendingError {
  #[snafu(display("Failed to get env variable"))]
  EnvVariable {
    #[snafu(source)]
    source: std::env::VarError,
    #[snafu(implicit)]
    location: Location,

    variable: String,
  },

  #[snafu(display("Failed to process http request"))]
  ReqwestClient {
    #[snafu(source)]
    source: reqwest::Error,
    #[snafu(implicit)]
    location: Location,
    #[snafu(backtrace)]
    backtrace: Backtrace,
  },

  #[snafu(display("Invalid http header name: {}", name))]
  ReqwestHeaderName {
    name: String,
    #[snafu(source)]
    source: reqwest::header::InvalidHeaderName,
    #[snafu(implicit)]
    location: Location,
  },

  #[snafu(display("Invalid http header value: {}", value))]
  ReqwestHeaderValue {
    value: String,
    #[snafu(source)]
    source: reqwest::header::InvalidHeaderValue,
    #[snafu(implicit)]
    location: Location,
  },

  #[snafu(display("Failed to serialize JSON"))]
  SerializeJson {
    #[snafu(source)]
    source: serde_json::Error,
    #[snafu(implicit)]
    location: Location,
  },

  #[snafu(display("Failed to deserialize JSON"))]
  DeserializeJson {
    #[snafu(source)]
    source: serde_json::Error,
    #[snafu(implicit)]
    location: Location,
  },

  #[snafu(display("{}", message))]
  PlainMessage {
    message: String,
    #[snafu(implicit)]
    location: Location,
  },
  // #[snafu(display("Impossible error!"))]
  // Impossible {
  // #[snafu(implicit)]
  // location: Location,
  // },
}
