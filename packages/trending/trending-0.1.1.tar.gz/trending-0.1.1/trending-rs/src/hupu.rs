use reqwest::Client as AsyncClient;
#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blocking")]
use crate::common::block_http_get;
use crate::{
  common::{EmptyType, PlatformType, TrendingRes, TrendingsRes, http_get},
  errors::Result,
};

pub const TRENDING_ENDPOINT: &'static str =
  "https://m.hupu.com/api/v2/bbs/topicThreads?topicId=1&page=1";

pub async fn trending(client: &AsyncClient) -> Result<TrendingsRes> {
  http_get::<EmptyType, EmptyType, HupuRes>(client, TRENDING_ENDPOINT, None, None, None)
    .await
    .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn blocking_trending(client: &BlockClient) -> Result<TrendingsRes> {
  block_http_get::<EmptyType, EmptyType, HupuRes>(client, TRENDING_ENDPOINT, None, None, None)
    .map(|r| r.into())
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct HupuRes {
  #[serde(rename = "data")]
  data: HupuData,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct HupuData {
  #[serde(
    rename = "topicThreads",
    skip_serializing_if = "Vec::is_empty",
    default
  )]
  threads: Vec<HupuThread>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct HupuThread {
  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "url")]
  url: String,
}

impl From<HupuThread> for TrendingRes {
  fn from(value: HupuThread) -> Self {
    Self {
      title: value.title,
      url: value.url,
      trend: None,
    }
  }
}

impl From<HupuRes> for TrendingsRes {
  fn from(value: HupuRes) -> Self {
    Self {
      platform: PlatformType::Hupu,
      result: value.data.threads.into_iter().map(|r| r.into()).collect(),
    }
  }
}
