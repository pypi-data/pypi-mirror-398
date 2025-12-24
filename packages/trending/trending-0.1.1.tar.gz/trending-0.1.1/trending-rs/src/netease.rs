use reqwest::Client as AsyncClient;
#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blocking")]
use crate::common::block_http_get;
use crate::{
  common::{
    EmptyType, MediaData, PageParam, PlatformType, SearchReq, SearchRes, SearchesRes, TrendingRes,
    TrendingsRes, http_get,
  },
  errors::Result,
};

pub const TRENDING_ENDPOINT: &'static str = "https://m.163.com/fe/api/hot/news/flow";
pub const SEARCH_ENDPOINT: &'static str =
  "https://gw.m.163.com/nc/api/v1/pc-wap/search?from=wap&needPcUrl=true";

pub async fn trending(client: &AsyncClient) -> Result<TrendingsRes> {
  http_get::<EmptyType, EmptyType, NeteaseTrendingRes>(client, TRENDING_ENDPOINT, None, None, None)
    .await
    .map(|r| r.into())
}

pub async fn search(client: &AsyncClient, req: &SearchReq) -> Result<SearchesRes> {
  http_get::<NeteaseSearchReq, EmptyType, NeteaseSearchRes>(
    client,
    SEARCH_ENDPOINT,
    None,
    Some(&req.into()),
    None,
  )
  .await
  .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn blocking_trending(client: &BlockClient) -> Result<TrendingsRes> {
  block_http_get::<EmptyType, EmptyType, NeteaseTrendingRes>(
    client,
    TRENDING_ENDPOINT,
    None,
    None,
    None,
  )
  .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn blocking_search(client: &BlockClient, req: &SearchReq) -> Result<SearchesRes> {
  block_http_get::<NeteaseSearchReq, EmptyType, NeteaseSearchRes>(
    client,
    SEARCH_ENDPOINT,
    None,
    Some(&req.into()),
    None,
  )
  .map(|r| r.into())
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseTrendingRes {
  #[serde(rename = "data")]
  data: NeteaseTrendingData,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseTrendingData {
  #[serde(rename = "list")]
  list: Vec<NeteaseTrendingNews>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseTrendingNews {
  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "url")]
  url: String,
}

impl From<NeteaseTrendingNews> for TrendingRes {
  fn from(value: NeteaseTrendingNews) -> Self {
    Self {
      title: value.title,
      url: value.url,
      trend: None,
    }
  }
}

impl From<NeteaseTrendingRes> for TrendingsRes {
  fn from(value: NeteaseTrendingRes) -> Self {
    Self {
      platform: PlatformType::Netease,
      result: value.data.list.into_iter().map(|r| r.into()).collect(),
    }
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseSearchReq<'a> {
  #[serde(rename = "query")]
  query: &'a str,

  #[serde(rename = "page", skip_serializing_if = "Option::is_none")]
  page: Option<u32>,

  #[serde(rename = "size", skip_serializing_if = "Option::is_none")]
  size: Option<u32>,

  #[serde(rename = "queryId", skip_serializing_if = "Option::is_none")]
  query_id: Option<&'a str>,
}

impl<'a> NeteaseSearchReq<'a> {
  fn convert_page_param(page: &PageParam) -> u32 {
    match page {
      PageParam::First => 0,
      PageParam::Other(page) => *page,
    }
  }
}

impl<'a> From<&'a SearchReq> for NeteaseSearchReq<'a> {
  fn from(value: &'a SearchReq) -> Self {
    Self {
      query: value.keyword.as_ref(),
      page: value.page.as_ref().map(Self::convert_page_param),
      size: value.size,
      query_id: if value.page.is_none() && value.size.is_none() {
        None
      } else {
        Some("DEFAULT")
      },
    }
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseSearchRes {
  #[serde(rename = "data")]
  data: NeteaseSearchData,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseSearchData {
  #[serde(rename = "result", skip_serializing_if = "Vec::is_empty", default)]
  result: Vec<NeteaseSearchResult>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct NeteaseSearchResult {
  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "pcUrl")]
  url: String,

  #[serde(rename = "ptime")]
  time: String,

  #[serde(rename = "imgurl", skip_serializing_if = "Option::is_none", default)]
  img_url: Option<Vec<String>>,
}

impl From<NeteaseSearchResult> for SearchRes {
  fn from(value: NeteaseSearchResult) -> Self {
    Self {
      title: value.title.replace("<em>", "").replace("</em>", ""),
      url: value.url,
      time: Some(1),
      medias: value
        .img_url
        .map(|s| s.into_iter().map(|m| MediaData::new_image(m)).collect()),
    }
  }
}

impl From<NeteaseSearchRes> for SearchesRes {
  fn from(value: NeteaseSearchRes) -> Self {
    Self {
      platform: PlatformType::Netease,
      result: value.data.result.into_iter().map(|r| r.into()).collect(),
    }
  }
}
