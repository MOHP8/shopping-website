// loading.js

// 顯示全局 Loading 提示
function showGlobalLoading() {
    const globalLoadingOverlay = document.getElementById('global-loading-overlay');
    if (globalLoadingOverlay) {
        globalLoadingOverlay.style.display = 'flex';
    }
}

// 隱藏全局 Loading 提示
function hideGlobalLoading() {
    const globalLoadingOverlay = document.getElementById('global-loading-overlay');
    if (globalLoadingOverlay) {
        globalLoadingOverlay.style.display = 'none';
    }
}

// // 在頁面載入時顯示全局 Loading
// document.addEventListener('DOMContentLoaded', function () {
//     showGlobalLoading();

//     // 在這裡可以進行其他相關的初始化邏輯或處理

//     // 實際載入完成時，例如，當所有資源都載入完成時
//     window.addEventListener('load', function () {
//         // 隱藏 Loading
//         hideGlobalLoading();
//     });
// });


//html 放入即可飲用
// <!-- Loading 提示的 HTML 內容 -->
// <div id="global-loading-overlay" style="display: none;">
//   <div id="global-loading-content">
//       <!-- 插入動態 GIF 圖片 -->
//       <img src="/static/img/loading.gif" alt="Loading..." />
//   </div>
// </div>


// // Loading 提示的 CSS 樣式
// <style>
//   #global-loading-overlay {
//       display: flex;
//       align-items: center;
//       justify-content: center;
//       position: fixed;
//       top: 0;
//       left: 0;
//       width: 100%;
//       height: 100%;
//       background-color: rgba(255, 255, 255, 0.8); /* 半透明白色背景 */
//       z-index: 9999; /* 保證在最上層 */
//   }

//   #global-loading-content {
//       background-color: #fff;
//       padding: 20px;
//   }
// </style>