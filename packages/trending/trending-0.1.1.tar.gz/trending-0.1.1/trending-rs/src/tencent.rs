use reqwest::Client as AsyncClient;
#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blocking")]
use crate::common::block_http_get;
#[cfg(feature = "blocking")]
use crate::common::block_http_post;
use crate::{
  common::{
    EmptyType, HttpBody, MediaData, PageParam, PlatformType, SearchReq, SearchRes, SearchesRes,
    TrendingRes, TrendingsRes, http_get, http_post,
  },
  errors::Result,
};

pub const TRENDING_ENDPOINT: &'static str =
  "https://r.inews.qq.com/gw/event/hot_ranking_list?page_size=30";

pub const SEARCH_ENDPOINT: &'static str = "https://i.news.qq.com/gw/pc_search/result";

pub async fn trending(client: &AsyncClient) -> Result<TrendingsRes> {
  http_get::<EmptyType, EmptyType, TencentTrendingRes>(client, TRENDING_ENDPOINT, None, None, None)
    .await
    .map(|r| r.into())
}

pub async fn search(client: &AsyncClient, req: &SearchReq) -> Result<SearchesRes> {
  http_post::<EmptyType, TencentSearchReq, TencentSearchRes>(
    client,
    SEARCH_ENDPOINT,
    None,
    None,
    Some(HttpBody::form(&req.into())),
  )
  .await
  .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn blocking_trending(client: &BlockClient) -> Result<TrendingsRes> {
  block_http_get::<EmptyType, EmptyType, TencentTrendingRes>(
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
  block_http_post::<EmptyType, TencentSearchReq, TencentSearchRes>(
    client,
    SEARCH_ENDPOINT,
    None,
    None,
    Some(HttpBody::form(&req.into())),
  )
  .map(|r| r.into())
}

#[allow(dead_code)]
#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentTrendingReq {
  #[serde(rename = "offset", skip_serializing_if = "Option::is_none")]
  offset: Option<u32>,

  #[serde(rename = "page_size", skip_serializing_if = "Option::is_none")]
  size: Option<u32>,

  #[serde(rename = "appver", skip_serializing_if = "Option::is_none")]
  app_ver: Option<String>,

  #[serde(rename = "rank_id", skip_serializing_if = "Option::is_none")]
  rank_id: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentTrendingRes {
  #[serde(rename = "idlist", skip_serializing_if = "Vec::is_empty", default)]
  list: Vec<TencentTrendingList>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentTrendingList {
  #[serde(rename = "newslist", skip_serializing_if = "Vec::is_empty", default)]
  news: Vec<TencentTrendingNews>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentTrendingNews {
  #[serde(rename = "id")]
  id: String,

  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "surl")]
  url: Option<String>,

  #[serde(rename = "ranking")]
  ranking: Option<u32>,
}

impl From<TencentTrendingNews> for TrendingRes {
  fn from(value: TencentTrendingNews) -> Self {
    Self {
      title: value.title,
      url: value.url.unwrap_or_else(String::new),
      trend: value.ranking.map(|r| r.to_string()),
    }
  }
}

impl From<TencentTrendingRes> for TrendingsRes {
  fn from(value: TencentTrendingRes) -> Self {
    Self {
      platform: PlatformType::Tencent,
      result: value
        .list
        .into_iter()
        .flat_map(|r| r.news.into_iter())
        .filter(|r| r.url.is_some())
        .map(|r| r.into())
        .collect(),
    }
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentSearchReq<'a> {
  #[serde(rename = "query")]
  query: &'a str,

  #[serde(rename = "is_pc")]
  is_pc: u32,

  #[serde(rename = "search_type")]
  search_type: &'a str,

  #[serde(rename = "page", skip_serializing_if = "Option::is_none")]
  page: Option<u32>,

  #[serde(
    rename = "hippy_custom_version",
    skip_serializing_if = "Option::is_none"
  )]
  hippy_custom_version: Option<&'a str>,

  #[serde(rename = "search_count_limit", skip_serializing_if = "Option::is_none")]
  search_count_limit: Option<u32>,

  #[serde(rename = "appver", skip_serializing_if = "Option::is_none")]
  app_ver: Option<&'a str>,
}

impl<'a> TencentSearchReq<'a> {
  fn convert_page_param(page: &PageParam) -> u32 {
    match page {
      PageParam::First => 0,
      PageParam::Other(page) => *page,
    }
  }
}

impl<'a> From<&'a SearchReq> for TencentSearchReq<'a> {
  fn from(value: &'a SearchReq) -> Self {
    Self {
      query: &value.keyword,
      is_pc: 1,
      search_type: "all",
      page: value.page.as_ref().map(Self::convert_page_param),
      hippy_custom_version: None,
      search_count_limit: value.size,
      app_ver: None,
    }
  }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentSearchRes {
  #[serde(rename = "secList", skip_serializing_if = "Vec::is_empty", default)]
  list: Vec<TencentSearchList>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentSearchList {
  #[serde(rename = "secType")]
  sec_type: u32,

  #[serde(rename = "newsList", skip_serializing_if = "Vec::is_empty", default)]
  news_list: Vec<TencentSearchNews>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TencentSearchNews {
  #[serde(rename = "id")]
  id: String,

  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "surl")]
  url: String,

  #[serde(rename = "timestamp")]
  timestamp: u64,

  #[serde(rename = "asbstract", skip_serializing_if = "Option::is_none")]
  desc: Option<String>,

  #[serde(rename = "thumbnails_qqnews", skip_serializing_if = "Option::is_none")]
  thumbnail: Option<Vec<String>>,
}

impl From<TencentSearchNews> for SearchRes {
  fn from(value: TencentSearchNews) -> Self {
    Self {
      title: value.title,
      url: value.url,
      time: Some(value.timestamp),
      medias: value
        .thumbnail
        .map(|s| s.into_iter().map(|m| MediaData::new_image(m)).collect()),
    }
  }
}

impl From<TencentSearchRes> for SearchesRes {
  fn from(value: TencentSearchRes) -> Self {
    Self {
      platform: PlatformType::Tencent,
      result: value
        .list
        .into_iter()
        .flat_map(|l| l.news_list.into_iter())
        .map(|r| r.into())
        .collect(),
    }
  }
}
