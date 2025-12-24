use std::fmt::Display;

#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use reqwest::{Client as AsyncClient, Method, header::HeaderMap};
use serde::{Deserialize, Serialize};
use snafu::ResultExt;

use crate::errors::{ReqwestClientSnafu, Result};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum PlatformType {
  #[serde(rename = "zhihu")]
  Zhihu,

  #[serde(rename = "weibo")]
  Weibo,

  #[serde(rename = "toutiao")]
  Toutiao,

  #[serde(rename = "tencent")]
  Tencent,

  #[serde(rename = "tieba")]
  Tieba,

  #[serde(rename = "netease")]
  Netease,

  #[serde(rename = "hupu")]
  Hupu,

  #[serde(untagged)]
  Other(String),
}

impl PlatformType {
  pub fn to_str(&self) -> &str {
    match self {
      PlatformType::Zhihu => "zhihu",
      PlatformType::Weibo => "weibo",
      PlatformType::Toutiao => "toutiao",
      PlatformType::Tencent => "tencent",
      PlatformType::Tieba => "tieba",
      PlatformType::Netease => "netease",
      PlatformType::Hupu => "hupu",
      PlatformType::Other(other) => other.as_str(),
    }
  }
}

impl Display for PlatformType {
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
    write!(f, "{}", self.to_str())
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TrendingsRes {
  #[serde(rename = "platform")]
  pub platform: PlatformType,

  #[serde(rename = "trendings", skip_serializing_if = "Vec::is_empty", default)]
  pub result: Vec<TrendingRes>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TrendingRes {
  #[serde(rename = "title")]
  pub title: String,

  #[serde(rename = "url")]
  pub url: String,

  #[serde(rename = "trend")]
  pub trend: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SearchesRes {
  #[serde(rename = "platform")]
  pub platform: PlatformType,

  #[serde(rename = "searches", skip_serializing_if = "Vec::is_empty", default)]
  pub result: Vec<SearchRes>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum PageParam {
  First,
  Other(u32),
}

impl From<u32> for PageParam {
  fn from(value: u32) -> Self {
    Self::Other(value)
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SearchReq {
  #[serde(rename = "keyword")]
  pub keyword: String,

  #[serde(rename = "page")]
  pub page: Option<PageParam>,

  #[serde(rename = "size")]
  pub size: Option<u32>,
}

impl SearchReq {
  pub fn new(keyword: impl Into<String>) -> Self {
    Self {
      keyword: keyword.into(),
      page: None,
      size: None,
    }
  }

  pub fn with_page(mut self, page: impl Into<PageParam>) -> Self {
    self.page = Some(page.into());
    self
  }

  pub fn with_size(mut self, size: u32) -> Self {
    self.size = Some(size);
    self
  }
}

impl From<&str> for SearchReq {
  fn from(value: &str) -> Self {
    Self::new(value)
  }
}

impl From<(&str, u32)> for SearchReq {
  fn from(value: (&str, u32)) -> Self {
    Self::new(value.0).with_page(value.1)
  }
}

impl From<(&str, u32, u32)> for SearchReq {
  fn from(value: (&str, u32, u32)) -> Self {
    Self::new(value.0).with_page(value.1).with_size(value.2)
  }
}

impl From<String> for SearchReq {
  fn from(value: String) -> Self {
    Self::new(value)
  }
}

impl From<(String, u32)> for SearchReq {
  fn from(value: (String, u32)) -> Self {
    Self::new(value.0).with_page(value.1)
  }
}

impl From<(String, u32, u32)> for SearchReq {
  fn from(value: (String, u32, u32)) -> Self {
    Self::new(value.0).with_page(value.1).with_size(value.2)
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SearchRes {
  #[serde(rename = "title")]
  pub title: String,

  #[serde(rename = "url")]
  pub url: String,

  #[serde(rename = "time")]
  pub time: Option<u64>,

  #[serde(rename = "medias", skip_serializing_if = "Option::is_none")]
  pub medias: Option<Vec<MediaData>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MediaData {
  #[serde(rename = "url")]
  pub url: String,

  #[serde(rename = "kind")]
  pub kind: MediaType,

  #[serde(rename = "desc", skip_serializing_if = "Option::is_none", default)]
  pub desc: Option<String>,
}

impl MediaData {
  pub fn new_video(url: impl Into<String>) -> Self {
    Self {
      url: url.into(),
      kind: MediaType::Video,
      desc: None,
    }
  }

  pub fn new_audio(url: impl Into<String>) -> Self {
    Self {
      url: url.into(),
      kind: MediaType::Audio,
      desc: None,
    }
  }

  pub fn new_image(url: impl Into<String>) -> Self {
    Self {
      url: url.into(),
      kind: MediaType::Image,
      desc: None,
    }
  }

  pub fn with_desc(mut self, desc: impl Into<String>) -> Self {
    self.desc = Some(desc.into());
    self
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum MediaType {
  #[serde(rename = "video")]
  Video,

  #[serde(rename = "audio")]
  Audio,

  #[serde(rename = "image")]
  Image,

  #[serde(untagged)]
  Other(String),
}

impl MediaType {
  pub fn as_str(&self) -> &str {
    match self {
      MediaType::Video => "viode",
      MediaType::Audio => "audio",
      MediaType::Image => "image",
      MediaType::Other(other) => other.as_str(),
    }
  }
}

pub(crate) fn not_empty_str(text: Option<String>) -> Option<String> {
  return if let Some(s) = &text
    && !s.is_empty()
  {
    text
  } else {
    None
  };
}

pub(crate) async fn http_get<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &AsyncClient,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  http_execute(client, Method::GET, url, headers, queries, body).await
}

pub(crate) async fn http_post<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &AsyncClient,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  http_execute(client, Method::POST, url, headers, queries, body).await
}

async fn http_execute<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &AsyncClient,
  method: Method,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  let mut req = client.request(method, url);
  if let Some(headers) = headers {
    req = req.headers(headers);
  }
  if let Some(queries) = queries {
    req = req.query(queries);
  }
  if let Some(body) = body {
    match body {
      HttpBody::Json(json) => req = req.json(json),
      HttpBody::Form(form) => req = req.form(form),
    }
  }
  let res = req
    .send()
    .await
    .context(ReqwestClientSnafu)?
    .json::<R>()
    .await
    .context(ReqwestClientSnafu)?;
  Ok(res)
}

#[cfg(feature = "blocking")]
pub(crate) fn block_http_get<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &BlockClient,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  block_http_execute(client, Method::GET, url, headers, queries, body)
}

#[cfg(feature = "blocking")]
pub(crate) fn block_http_post<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &BlockClient,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  block_http_execute(client, Method::POST, url, headers, queries, body)
}

#[cfg(feature = "blocking")]
fn block_http_execute<
  Q: Serialize + ?Sized,
  B: Serialize + ?Sized,
  R: for<'de> Deserialize<'de>,
>(
  client: &BlockClient,
  method: Method,
  url: &str,
  headers: Option<HeaderMap>,
  queries: Option<&Q>,
  body: Option<HttpBody<&B>>,
) -> Result<R> {
  let mut req = client.request(method, url);
  if let Some(headers) = headers {
    req = req.headers(headers);
  }
  if let Some(queries) = queries {
    req = req.query(queries);
  }
  if let Some(body) = body {
    match body {
      HttpBody::Json(json) => req = req.json(&json),
      HttpBody::Form(form) => req = req.form(&form),
    }
  }
  let res = req
    .send()
    .context(ReqwestClientSnafu)?
    .json::<R>()
    .context(ReqwestClientSnafu)?;
  Ok(res)
}

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
pub(crate) struct EmptyType;

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
pub(crate) enum HttpBody<T> {
  Json(T),
  Form(T),
}

impl<T> HttpBody<T> {
  #[allow(dead_code)]
  pub(crate) fn json(json: T) -> HttpBody<T> {
    HttpBody::<T>::Json(json)
  }
  pub(crate) fn form(form: T) -> HttpBody<T> {
    HttpBody::Form(form)
  }
}
