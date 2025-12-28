import { app } from "../../scripts/app.js";
const styleMenus = `
    /* 隐藏Panel内容容器，但排除选择工具箱 */
    .p-panel:not(.selection-toolbox) .p-panel-content-container{
        display: none;
    }
    // .side-tool-bar-container.small-sidebar{
    //     display: none;
    // }
    .comfyui-menu.flex.items-center{
        display: none;
    }
    .p-dialog-mask.p-overlay-mask.p-overlay-mask-enter.p-dialog-bottomright{
        display: none !important;
    }
    body .bizyair-comfy-floating-button{
        display: none;
    }
    .bizy-select-title-container{
        display: none;
    }
    .workflow-tabs-container{
        display: none;
    }
    body .comfyui-body-bottom{
        display: none;
    }
    #comfyui-body-bottom{
        display: none;
    }
    /* 隐藏左侧的工作流按钮 */
    .p-button.p-component.p-button-icon-only.p-button-text.workflows-tab-button.side-bar-button.p-button-secondary{
        display: none;
    }
    /* 隐藏左侧的输入输出按钮 */
    .p-button.p-component.p-button-icon-only.p-button-text.mtb-inputs-outputs-tab-button.side-bar-button.p-button-secondary{
        display: none;
    }
    body div.side-tool-bar-end{
        display: none;
    }
    body .tydev-utils-log-console-container{
        display: none;
    }
    .p-dialog-mask.p-overlay-mask.p-overlay-mask-enter[data-pc-name="dialog"]{
        display: none !important;
    }
    .p-button.p-component.p-button-icon-only.p-button-text.templates-tab-button.side-bar-button.p-button-secondary{
        display: none;
    }
    .p-button.p-component.p-button-icon-only.p-button-text.queue-tab-button.side-bar-button.p-button-secondary{
        display: none;
    }
    .w-full.flex.content-end{
        display: none;
    }
    .side-tool-bar-container.small-sidebar .side-bar-button-label{
        display: none;
    }
    /* 隐藏整个comfy-menu-button-wrapper元素 */
    .comfy-menu-button-wrapper{
        display: none;
    }
    /* 隐藏帮助中心按钮 */
    .comfy-help-center-btn{
        display: none;
    }
    /* 隐藏底部面板(Console)按钮 */
    button[aria-label="底部面板"]{
        display: none;
    }
    /* 隐藏键盘快捷键按钮 */
    button[aria-label^="键盘快捷键"]{
        display: none;
    }
    /* 隐藏右下角按钮组(包含鼠标指针、适应视图、缩放控制、小地图、隐藏链接等按钮) */
    .p-buttongroup.absolute.right-0.bottom-0{
        display: none;
    }
    .pointer-events-auto.relative.w-full.h-10.bg-gradient-to-r.from-blue-600.to-blue-700.flex.items-center.justify-center.px-4 {
        display: none;
    }
    .p-splitterpanel.p-splitterpanel-nested.flex.flex-col .ml-1.flex.pt-1{
        display: none;
    }
    .p-button.p-component.p-button-text.size-8.bg-primary-background.text-white.p-0{
        display: none;
    }
    .p-button.p-component.p-button-secondary.p-button-text.h-8.w-8.px-0{
        display: none;
    }

    /* 隐藏左侧的资产按钮 */
    .p-button.p-component.p-button-icon-only.p-button-text.assets-tab-button.side-bar-button.p-button-secondary {
        display: none;
    }
    /* 隐藏左侧的模型库按钮 */
    .p-button.p-component.p-button-icon-only.p-button-text.model-library-tab-button.side-bar-button.p-button-secondary{
        display: none;
    }
    body .comfy-img-preview video{
      width: 100%;
      height: 100%;
    }
    button[aria-label^="设置 (Ctrl + ,)"]{
      display: none;
    }
    body .p-toast-message.p-toast-message-error{
        display: none;
    }
    body .bizyair-toaster-container{
        display: none;
    }

`;
app.registerExtension({
  name: "comfy.BizyAir.Style",
  async setup() {
    const styleElement = document.createElement("style");
    styleElement.textContent = styleMenus;
    document.head.appendChild(styleElement);
    const getCloseBtn = () => {
      // let temp = null
      // document.querySelectorAll('h2').forEach(e => {
      //     if (e.innerHTML == "<span>模板</span>") {
      //         const dialogContent = e.closest('.p-dialog-content')
      //         if (dialogContent) {
      //             temp = dialogContent.querySelector('i.pi.pi-times.text-sm')
      //         }
      //     }
      // })
      return document.querySelector("i.pi.pi-times.text-sm");
    };
    const getFengrossmentBtn = () => {
      let temp = null;
      document.querySelectorAll("button").forEach((e) => {
        if (e.getAttribute("aria-label") == "专注模式 (F)") {
          temp = e;
        }
      });
      return temp;
    };
    let indexCloseLayout = 0;
    let indexAddSmlBar = 0;
    let indexFengrossment = 0;
    let iTimer = setInterval(() => {
      indexCloseLayout++;
      if (indexCloseLayout > 10) {
        clearInterval(iTimer);
        return;
      }
      if (getCloseBtn()) {
        getCloseBtn().click();
        clearInterval(iTimer);
      }
    }, 300);
    let iTimerSmlBar = setInterval(() => {
      indexAddSmlBar++;
      if (indexAddSmlBar > 10) {
        clearInterval(iTimerSmlBar);
        return;
      }
      if (document.querySelector(".side-tool-bar-container")) {
        document
          .querySelector(".side-tool-bar-container")
          .classList.add("small-sidebar");
        clearInterval(iTimerSmlBar);
      }
    }, 300);
    let iTimerFengrossment = setInterval(() => {
      indexFengrossment++;
      if (indexFengrossment > 10) {
        clearInterval(iTimerFengrossment);
        return;
      }
      if (getFengrossmentBtn()) {
        getFengrossmentBtn().style.display = "none";
        clearInterval(iTimerFengrossment);
      }
    }, 300);
  },
});
