use std::time::Duration;

#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockHttpClient;
use reqwest::{
  Client as AsyncHttpClient, Proxy,
  header::{AsHeaderName, HeaderMap, HeaderName, HeaderValue},
};
use snafu::ResultExt;

use crate::{
  common::{SearchReq, SearchesRes, TrendingsRes},
  errors::{ReqwestClientSnafu, Result},
};

pub struct AsyncClient {
  client: AsyncHttpClient,
}

impl AsyncClient {
  pub fn new() -> Self {
    let client = AsyncHttpClient::new();
    Self { client }
  }

  pub fn new_with_options(options: ClientOptions) -> Result<Self> {
    let mut client_builder = AsyncHttpClient::builder();
    if let Some(timeout) = options.timeout {
      client_builder = client_builder.timeout(timeout);
    }
    if let Some(proxy) = options.proxy {
      client_builder = client_builder.proxy(proxy);
    }
    let client = client_builder
      .default_headers(options.headers)
      .build()
      .context(ReqwestClientSnafu)?;
    Ok(AsyncClient { client })
  }

  pub async fn trending_zhihu(&self) -> Result<TrendingsRes> {
    crate::zhihu::trending(&self.client).await
  }

  pub async fn trending_weibo(&self) -> Result<TrendingsRes> {
    crate::weibo::trending(&self.client).await
  }

  pub async fn trending_toutiao(&self) -> Result<TrendingsRes> {
    crate::toutiao::trending(&self.client).await
  }

  pub async fn trending_tencent(&self) -> Result<TrendingsRes> {
    crate::tencent::trending(&self.client).await
  }

  pub async fn search_tencent(&self, req: &SearchReq) -> Result<SearchesRes> {
    crate::tencent::search(&self.client, req).await
  }

  pub async fn trending_tieba(&self) -> Result<TrendingsRes> {
    crate::tieba::trending(&self.client).await
  }

  pub async fn trending_netease(&self) -> Result<TrendingsRes> {
    crate::netease::trending(&self.client).await
  }

  pub async fn search_netease(&self, req: &SearchReq) -> Result<SearchesRes> {
    crate::netease::search(&self.client, req).await
  }

  pub async fn trending_hupu(&self) -> Result<TrendingsRes> {
    crate::hupu::trending(&self.client).await
  }
}

#[cfg(feature = "blocking")]
pub struct BlockClient {
  client: BlockHttpClient,
}

#[cfg(feature = "blocking")]
impl BlockClient {
  pub fn new() -> Self {
    let client = BlockHttpClient::new();
    Self { client }
  }

  pub fn new_with_options(options: ClientOptions) -> Result<Self> {
    let mut client_builder = BlockHttpClient::builder();
    if let Some(timeout) = options.timeout {
      client_builder = client_builder.timeout(timeout);
    }
    if let Some(proxy) = options.proxy {
      client_builder = client_builder.proxy(proxy);
    }
    let client = client_builder
      .default_headers(options.headers)
      .build()
      .context(ReqwestClientSnafu)?;
    Ok(BlockClient { client })
  }

  pub fn trending_zhihu(&self) -> Result<TrendingsRes> {
    crate::zhihu::block_trending(&self.client)
  }

  pub fn trending_weibo(&self) -> Result<TrendingsRes> {
    crate::weibo::block_trending(&self.client)
  }

  pub fn trending_toutiao(&self) -> Result<TrendingsRes> {
    crate::toutiao::blocking_trending(&self.client)
  }

  pub fn trending_tencent(&self) -> Result<TrendingsRes> {
    crate::tencent::blocking_trending(&self.client)
  }

  pub fn search_tencent(&self, query: &SearchReq) -> Result<SearchesRes> {
    crate::tencent::blocking_search(&self.client, query)
  }

  pub fn trending_tieba(&self) -> Result<TrendingsRes> {
    crate::tieba::blocking_trending(&self.client)
  }

  pub fn trending_netease(&self) -> Result<TrendingsRes> {
    crate::netease::blocking_trending(&self.client)
  }

  pub fn search_netease(&self, query: &SearchReq) -> Result<SearchesRes> {
    crate::netease::blocking_search(&self.client, query)
  }

  pub fn trending_hupu(&self) -> Result<TrendingsRes> {
    crate::hupu::blocking_trending(&self.client)
  }
}

#[derive(Debug, Clone)]
pub struct ClientOptions {
  pub headers: HeaderMap,
  pub timeout: Option<Duration>,
  pub proxy: Option<Proxy>,
}

impl ClientOptions {
  pub fn new() -> ClientOptions {
    ClientOptions {
      headers: HeaderMap::new(),
      timeout: None,
      proxy: None,
    }
  }

  pub fn with_headers(mut self, headers: HeaderMap) -> Self {
    self.headers.extend(headers);
    self
  }

  pub fn with_header(mut self, key: HeaderName, value: HeaderValue) -> Self {
    self.headers.insert(key, value);
    self
  }

  pub fn with_proxy(mut self, proxy: Proxy) -> Self {
    self.proxy = Some(proxy);
    self
  }

  pub fn with_timeout(mut self, timeout: Duration) -> Self {
    self.timeout = Some(timeout);
    self
  }

  pub fn contains_header(&self, key: impl AsHeaderName) -> bool {
    self.headers.contains_key(key)
  }
}
