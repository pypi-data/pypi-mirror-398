use tokio;
use trending::{client::AsyncClient, common::SearchReq, errors::Result};

#[tokio::main(flavor = "current_thread")]
async fn main() {
  match run_main().await {
    Ok(_) => std::process::exit(0),
    Err(err) => {
      eprintln!("{:?}", err);
    }
  }
}

async fn run_main() -> Result<()> {
  let client = AsyncClient::new();

  let req = SearchReq::new("ELON");
  let res = client.search_tencent(&req).await?;
  println!(
    "receive {} searches from {}",
    res.result.len(),
    res.platform
  );
  for (index, search) in res.result.iter().enumerate() {
    println!("{:2} -> {}", index, search.title);
  }
  Ok(())
}
