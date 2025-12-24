use pyo3::prelude::*;

#[pymodule]
mod trending {

  use std::{
    fmt::{Display, Formatter},
    str::FromStr,
    time::Duration,
  };

  use pyo3::{exceptions::PyOSError, prelude::*};
  use reqwest::{
    Proxy,
    header::{HeaderName, HeaderValue},
  };
  use snafu::ResultExt;
  use trending::{
    client::{BlockClient as RBlockClient, ClientOptions as RClientOptions},
    common::{
      MediaData as RMediaData, PageParam, SearchReq as RSearchReq, SearchRes as RSearchRes,
      SearchesRes as RSearchesRes, TrendingRes as RTrendingRes, TrendingsRes as RTrendingsRes,
    },
    errors::{
      ReqwestClientSnafu, ReqwestHeaderNameSnafu, ReqwestHeaderValueSnafu,
      TrendingError as RTrendingError,
    },
  };

  #[pyclass]
  #[derive(Debug)]
  pub struct TrendingError(RTrendingError);

  impl From<RTrendingError> for TrendingError {
    fn from(err: RTrendingError) -> Self {
      Self(err)
    }
  }

  impl From<TrendingError> for PyErr {
    fn from(err: TrendingError) -> Self {
      PyOSError::new_err(err.0.to_string())
    }
  }

  pub type Result<T> = std::result::Result<T, TrendingError>;

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct ClientOptions {
    options: RClientOptions,
  }

  impl Display for ClientOptions {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  #[pymethods]
  impl ClientOptions {
    #[new]
    pub fn new() -> Self {
      Self {
        options: RClientOptions::new(),
      }
    }

    pub fn with_header(&mut self, name: &str, value: &str) -> Result<()> {
      let name = HeaderName::from_str(name).context(ReqwestHeaderNameSnafu {
        name: name.to_string(),
      })?;
      let value = HeaderValue::from_str(value).context(ReqwestHeaderValueSnafu {
        value: value.to_string(),
      })?;
      self.options.headers.insert(name, value);
      Ok(())
    }

    pub fn with_proxy(&mut self, proxy: &str) -> Result<()> {
      let proxy = Proxy::all(proxy).context(ReqwestClientSnafu)?;
      self.options.proxy = Some(proxy);
      Ok(())
    }

    pub fn with_timeout(&mut self, timeout: Duration) {
      self.options.timeout = Some(timeout);
    }

    pub fn debug_print(&self) {
      println!("{:?}", self);
    }
  }

  #[pyclass]
  struct BlockClient {
    client: RBlockClient,
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct TrendingRes {
    #[pyo3(get, set)]
    title: String,

    #[pyo3(get, set)]
    url: String,

    #[pyo3(get, set)]
    trend: Option<String>,
  }

  impl From<RTrendingRes> for TrendingRes {
    fn from(value: RTrendingRes) -> Self {
      Self {
        title: value.title,
        url: value.url,
        trend: value.trend,
      }
    }
  }

  impl Display for TrendingRes {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct TrendingsRes {
    #[pyo3(get, set)]
    platform: String,

    #[pyo3(get, set)]
    result: Vec<TrendingRes>,
  }

  impl From<RTrendingsRes> for TrendingsRes {
    fn from(value: RTrendingsRes) -> Self {
      let result = value.result.into_iter().map(|r| r.into()).collect();
      Self {
        platform: value.platform.to_str().to_string(),
        result,
      }
    }
  }

  impl Display for TrendingsRes {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct SearchReq {
    #[pyo3(get, set)]
    keyword: String,

    #[pyo3(get, set)]
    page: Option<u32>,

    #[pyo3(get, set)]
    size: Option<u32>,
  }

  #[pymethods]
  impl SearchReq {
    #[new]
    #[pyo3(signature = (keyword, page = None, size = None))]
    pub fn new(keyword: &str, page: Option<u32>, size: Option<u32>) -> Self {
      Self {
        keyword: keyword.to_string(),
        page,
        size,
      }
    }
  }

  impl Display for SearchReq {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  impl From<SearchReq> for RSearchReq {
    fn from(value: SearchReq) -> Self {
      Self {
        keyword: value.keyword,
        page: value.page.map(|p| PageParam::Other(p)),
        size: value.size,
      }
    }
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct MediaData {
    #[pyo3(get, set)]
    url: String,

    #[pyo3(get, set)]
    kind: String,

    #[pyo3(get, set)]
    desc: Option<String>,
  }

  impl Display for MediaData {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  impl From<RMediaData> for MediaData {
    fn from(value: RMediaData) -> Self {
      Self {
        url: value.url,
        kind: value.kind.as_str().to_string(),
        desc: value.desc,
      }
    }
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct SearchRes {
    #[pyo3(get, set)]
    title: String,

    #[pyo3(get, set)]
    url: String,

    #[pyo3(get, set)]
    time: Option<u64>,

    #[pyo3(get, set)]
    medias: Option<Vec<MediaData>>,
  }

  impl Display for SearchRes {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  impl From<RSearchRes> for SearchRes {
    fn from(value: RSearchRes) -> Self {
      Self {
        title: value.title,
        url: value.url,
        time: value.time,
        medias: value
          .medias
          .map(|s| s.into_iter().map(|m| m.into()).collect()),
      }
    }
  }

  #[pyclass(str)]
  #[derive(Debug, Clone)]
  pub struct SearchesRes {
    #[pyo3(get, set)]
    platform: String,

    #[pyo3(get, set)]
    result: Vec<SearchRes>,
  }

  impl Display for SearchesRes {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
      write!(f, "{:?}", self)
    }
  }

  impl From<RSearchesRes> for SearchesRes {
    fn from(value: RSearchesRes) -> Self {
      Self {
        platform: value.platform.to_str().to_string(),
        result: value.result.into_iter().map(|r| r.into()).collect(),
      }
    }
  }

  #[pymethods]
  impl BlockClient {
    #[new]
    #[pyo3(signature = (options = None))]
    fn new(options: Option<ClientOptions>) -> Result<Self> {
      let client = if let Some(options) = options {
        RBlockClient::new_with_options(options.options)?
      } else {
        RBlockClient::new()
      };
      Ok(Self { client })
    }

    pub fn trending_zhihu(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_zhihu()?;
      Ok(res.into())
    }

    pub fn trending_weibo(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_weibo()?;
      Ok(res.into())
    }

    pub fn trending_toutiao(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_toutiao()?;
      Ok(res.into())
    }

    pub fn trending_tencent(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_tencent()?;
      Ok(res.into())
    }

    pub fn search_tecent(&self, req: SearchReq) -> Result<SearchesRes> {
      let req: RSearchReq = req.into();
      let res = self.client.search_tencent(&req)?;
      Ok(res.into())
    }

    pub fn trending_tieba(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_tieba()?;
      Ok(res.into())
    }

    pub fn trending_netease(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_netease()?;
      Ok(res.into())
    }

    pub fn search_netease(&self, req: SearchReq) -> Result<SearchesRes> {
      let req: RSearchReq = req.into();
      let res = self.client.search_netease(&req)?;
      Ok(res.into())
    }

    pub fn trending_hupu(&self) -> Result<TrendingsRes> {
      let res = self.client.trending_hupu()?;
      Ok(res.into())
    }
  }
}
