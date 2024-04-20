// 页面高度
const vh = window.innerHeight
let work_obj = {}

// 延迟
function delay(ms){
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function action() {
  let last_height = document.body.offsetHeight;
  window.scrollTo(0, window.scrollY + vh * 1.5)

  ul = 	document.querySelector('#userPostedFeeds').querySelectorAll('.cover')

  ul.forEach((e,index)=>{
    // length 为 0 时是图片，为 1 时为视频
    work_obj[e.href] = ul[index].querySelector('.play-icon') ? 1 : 0
  })
	// 延迟500ms
  await delay(500);
  // console.log(last_height, document.body.offsetHeight)

  // 判断是否滚动到底部
  if(document.body.offsetHeight > last_height){
    action()
  }else{
    console.log('end')
    // 作品的数量
    console.log(Object.keys(work_obj).length)

    // 转换格式，并下载为txt文件
    var content = JSON.stringify(work_obj);
    var blob = new Blob([content], {type: "text/plain;charset=utf-8"});
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "xhs_works.txt";
    link.click();
  }
}

action()