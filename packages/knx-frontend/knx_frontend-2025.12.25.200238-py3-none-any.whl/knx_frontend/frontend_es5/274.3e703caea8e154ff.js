"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["274"],{48565:function(e,t,i){i.d(t,{d:function(){return a}});var a=e=>{switch(e.language){case"cs":case"de":case"fi":case"fr":case"sk":case"sv":return" ";default:return""}}},485:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),r=i(69683),n=i(6454),l=i(25460),s=(i(28706),i(23418),i(62062),i(18111),i(61701),i(2892),i(26099),i(62826)),c=i(43306),d=i(96196),p=i(77845),u=i(94333),h=i(92542),v=i(89473),g=(i(60733),i(48565)),f=i(55376),m=i(78436),_=e([c,v]);[c,v]=_.then?(await _)():_;var y,b,k,$,A,M,w,x,F=e=>e,Z="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",z="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M13.5,16V19H10.5V16H8L12,12L16,16H13.5M13,9V3.5L18.5,9H13Z",H=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),n=0;n<i;n++)o[n]=arguments[n];return(e=(0,r.A)(this,t,[].concat(o))).multiple=!1,e.disabled=!1,e.uploading=!1,e.autoOpenFileDialog=!1,e._drag=!1,e}return(0,n.A)(t,e),(0,o.A)(t,[{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),this.autoOpenFileDialog&&this._openFilePicker()}},{key:"_name",get:function(){return void 0===this.value?"":"string"==typeof this.value?this.value:(this.value instanceof FileList?Array.from(this.value):(0,f.e)(this.value)).map((e=>e.name)).join(", ")}},{key:"render",value:function(){var e=this.localize||this.hass.localize;return(0,d.qy)(y||(y=F`
      ${0}
    `),this.uploading?(0,d.qy)(b||(b=F`<div class="container">
            <div class="uploading">
              <span class="header"
                >${0}</span
              >
              ${0}
            </div>
            <mwc-linear-progress
              .indeterminate=${0}
              .progress=${0}
            ></mwc-linear-progress>
          </div>`),this.uploadingLabel||(this.value?e("ui.components.file-upload.uploading_name",{name:this._name}):e("ui.components.file-upload.uploading")),this.progress?(0,d.qy)(k||(k=F`<div class="progress">
                    ${0}${0}%
                  </div>`),this.progress,this.hass&&(0,g.d)(this.hass.locale)):d.s6,!this.progress,this.progress?this.progress/100:void 0):(0,d.qy)($||($=F`<label
            for=${0}
            class="container ${0}"
            @drop=${0}
            @dragenter=${0}
            @dragover=${0}
            @dragleave=${0}
            @dragend=${0}
            >${0}
            <input
              id="input"
              type="file"
              class="file"
              .accept=${0}
              .multiple=${0}
              @change=${0}
          /></label>`),this.value?"":"input",(0,u.H)({dragged:this._drag,multiple:this.multiple,value:Boolean(this.value)}),this._handleDrop,this._handleDragStart,this._handleDragStart,this._handleDragEnd,this._handleDragEnd,this.value?"string"==typeof this.value?(0,d.qy)(M||(M=F`<div class="row">
                    <div class="value" @click=${0}>
                      <ha-svg-icon
                        .path=${0}
                      ></ha-svg-icon>
                      ${0}
                    </div>
                    <ha-icon-button
                      @click=${0}
                      .label=${0}
                      .path=${0}
                    ></ha-icon-button>
                  </div>`),this._openFilePicker,this.icon||z,this.value,this._clearValue,this.deleteLabel||e("ui.common.delete"),Z):(this.value instanceof FileList?Array.from(this.value):(0,f.e)(this.value)).map((t=>(0,d.qy)(w||(w=F`<div class="row">
                        <div class="value" @click=${0}>
                          <ha-svg-icon
                            .path=${0}
                          ></ha-svg-icon>
                          ${0} - ${0}
                        </div>
                        <ha-icon-button
                          @click=${0}
                          .label=${0}
                          .path=${0}
                        ></ha-icon-button>
                      </div>`),this._openFilePicker,this.icon||z,t.name,(0,m.A)(t.size),this._clearValue,this.deleteLabel||e("ui.common.delete"),Z))):(0,d.qy)(A||(A=F`<ha-button
                    size="small"
                    appearance="filled"
                    @click=${0}
                  >
                    <ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>
                    ${0}
                  </ha-button>
                  <span class="secondary"
                    >${0}</span
                  >
                  <span class="supports">${0}</span>`),this._openFilePicker,this.icon||z,this.label||e("ui.components.file-upload.label"),this.secondary||e("ui.components.file-upload.secondary"),this.supports),this.accept,this.multiple,this._handleFilePicked))}},{key:"_openFilePicker",value:function(){var e;null===(e=this._input)||void 0===e||e.click()}},{key:"_handleDrop",value:function(e){var t;e.preventDefault(),e.stopPropagation(),null!==(t=e.dataTransfer)&&void 0!==t&&t.files&&(0,h.r)(this,"file-picked",{files:this.multiple||1===e.dataTransfer.files.length?Array.from(e.dataTransfer.files):[e.dataTransfer.files[0]]}),this._drag=!1}},{key:"_handleDragStart",value:function(e){e.preventDefault(),e.stopPropagation(),this._drag=!0}},{key:"_handleDragEnd",value:function(e){e.preventDefault(),e.stopPropagation(),this._drag=!1}},{key:"_handleFilePicked",value:function(e){0!==e.target.files.length&&(this.value=e.target.files,(0,h.r)(this,"file-picked",{files:e.target.files}))}},{key:"_clearValue",value:function(e){e.preventDefault(),this._input.value="",this.value=void 0,(0,h.r)(this,"change"),(0,h.r)(this,"files-cleared")}}])}(d.WF);H.styles=(0,d.AH)(x||(x=F`
    :host {
      display: block;
      height: 240px;
    }
    :host([disabled]) {
      pointer-events: none;
      color: var(--disabled-text-color);
    }
    .container {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      border: solid 1px
        var(--mdc-text-field-idle-line-color, rgba(0, 0, 0, 0.42));
      border-radius: var(--mdc-shape-small, var(--ha-border-radius-sm));
      height: 100%;
    }
    .row {
      display: flex;
      align-items: center;
    }
    label.container {
      border: dashed 1px
        var(--mdc-text-field-idle-line-color, rgba(0, 0, 0, 0.42));
      cursor: pointer;
    }
    .container .uploading {
      display: flex;
      flex-direction: column;
      width: 100%;
      align-items: flex-start;
      padding: 0 32px;
      box-sizing: border-box;
    }
    :host([disabled]) .container {
      border-color: var(--disabled-color);
    }
    label:hover,
    label.dragged {
      border-style: solid;
    }
    label.dragged {
      border-color: var(--primary-color);
    }
    .dragged:before {
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      background-color: var(--primary-color);
      content: "";
      opacity: var(--dark-divider-opacity);
      pointer-events: none;
      border-radius: var(--mdc-shape-small, 4px);
    }
    label.value {
      cursor: default;
    }
    label.value.multiple {
      justify-content: unset;
      overflow: auto;
    }
    .highlight {
      color: var(--primary-color);
    }
    ha-button {
      margin-bottom: 8px;
    }
    .supports {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s);
    }
    :host([disabled]) .secondary {
      color: var(--disabled-text-color);
    }
    input.file {
      display: none;
    }
    .value {
      cursor: pointer;
    }
    .value ha-svg-icon {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
    ha-button {
      --mdc-button-outline-color: var(--primary-color);
      --mdc-icon-button-size: 24px;
    }
    mwc-linear-progress {
      width: 100%;
      padding: 8px 32px;
      box-sizing: border-box;
    }
    .header {
      font-weight: var(--ha-font-weight-medium);
    }
    .progress {
      color: var(--secondary-text-color);
    }
    button.link {
      background: none;
      border: none;
      padding: 0;
      font-size: var(--ha-font-size-m);
      color: var(--primary-color);
      text-decoration: underline;
      cursor: pointer;
    }
  `)),(0,s.__decorate)([(0,p.MZ)({attribute:!1})],H.prototype,"hass",void 0),(0,s.__decorate)([(0,p.MZ)({attribute:!1})],H.prototype,"localize",void 0),(0,s.__decorate)([(0,p.MZ)()],H.prototype,"accept",void 0),(0,s.__decorate)([(0,p.MZ)()],H.prototype,"icon",void 0),(0,s.__decorate)([(0,p.MZ)()],H.prototype,"label",void 0),(0,s.__decorate)([(0,p.MZ)()],H.prototype,"secondary",void 0),(0,s.__decorate)([(0,p.MZ)({attribute:"uploading-label"})],H.prototype,"uploadingLabel",void 0),(0,s.__decorate)([(0,p.MZ)({attribute:"delete-label"})],H.prototype,"deleteLabel",void 0),(0,s.__decorate)([(0,p.MZ)()],H.prototype,"supports",void 0),(0,s.__decorate)([(0,p.MZ)({type:Object})],H.prototype,"value",void 0),(0,s.__decorate)([(0,p.MZ)({type:Boolean})],H.prototype,"multiple",void 0),(0,s.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],H.prototype,"disabled",void 0),(0,s.__decorate)([(0,p.MZ)({type:Boolean})],H.prototype,"uploading",void 0),(0,s.__decorate)([(0,p.MZ)({type:Number})],H.prototype,"progress",void 0),(0,s.__decorate)([(0,p.MZ)({type:Boolean,attribute:"auto-open-file-dialog"})],H.prototype,"autoOpenFileDialog",void 0),(0,s.__decorate)([(0,p.wk)()],H.prototype,"_drag",void 0),(0,s.__decorate)([(0,p.P)("#input")],H.prototype,"_input",void 0),H=(0,s.__decorate)([(0,p.EM)("ha-file-upload")],H),t()}catch(P){t(P)}}))},41881:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),o=i(50264),r=i(44734),n=i(56038),l=i(75864),s=i(69683),c=i(6454),d=(i(28706),i(74423),i(2892),i(26099),i(38781),i(62826)),p=i(96196),u=i(77845),h=i(92542),v=i(39396),g=i(872),f=i(10234),m=i(94161),_=i(89473),y=i(485),b=i(1214),k=e([_,y]);[_,y]=k.then?(await k)():k;var $,A,M,w,x,F=e=>e,Z=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,n=new Array(i),c=0;c<i;c++)n[c]=arguments[c];return(e=(0,s.A)(this,t,[].concat(n))).value=null,e.crop=!1,e.selectMedia=!1,e.fullMedia=!1,e.original=!1,e.size=512,e._uploading=!1,e._chooseMedia=()=>{var t;(0,b.O)((0,l.A)(e),{action:"pick",entityId:"browser",accept:["image/*"],navigateIds:e.fullMedia?void 0:[{media_content_id:void 0,media_content_type:void 0},{media_content_id:g.AP,media_content_type:"app"}],minimumNavigateLevel:e.fullMedia?void 0:2,hideContentType:!0,contentIdHelper:e.contentIdHelper,mediaPickedCallback:(t=(0,o.A)((0,a.A)().m((function t(i){var o,r,n,s,c,d;return(0,a.A)().w((function(t){for(;;)switch(t.p=t.n){case 0:if(!e.fullMedia){t.n=1;break}return(0,h.r)((0,l.A)(e),"media-picked",i),t.a(2);case 1:if(!(o=(0,g.pD)(i.item.media_content_id))){t.n=7;break}if(!e.crop){t.n=6;break}return r=(0,g.Q0)(o,void 0,!0),t.p=2,t.n=3,(0,g.M5)(e.hass,r);case 3:n=t.v,t.n=5;break;case 4:return t.p=4,d=t.v,(0,f.K$)((0,l.A)(e),{text:d.toString()}),t.a(2);case 5:s={type:i.item.media_content_type},c=new File([n],i.item.title,s),e._cropFile(c,o),t.n=7;break;case 6:e.value=(0,g.Q0)(o,e.size,e.original),(0,h.r)((0,l.A)(e),"change");case 7:return t.a(2)}}),t,null,[[2,4]])}))),function(e){return t.apply(this,arguments)})})},e}return(0,c.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){if(!this.value){var e=this.secondary||(this.selectMedia?(0,p.qy)($||($=F`${0}`),this.hass.localize("ui.components.picture-upload.secondary",{select_media:(0,p.qy)(A||(A=F`<button
                  class="link"
                  @click=${0}
                >
                  ${0}
                </button>`),this._chooseMedia,this.hass.localize("ui.components.picture-upload.select_media"))})):void 0);return(0,p.qy)(M||(M=F`
        <ha-file-upload
          .hass=${0}
          .icon=${0}
          .label=${0}
          .secondary=${0}
          .supports=${0}
          .uploading=${0}
          @file-picked=${0}
          @change=${0}
          accept="image/png, image/jpeg, image/gif"
        ></ha-file-upload>
      `),this.hass,"M18 15V18H15V20H18V23H20V20H23V18H20V15H18M13.3 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H19C20.1 3 21 3.9 21 5V13.3C20.4 13.1 19.7 13 19 13C17.9 13 16.8 13.3 15.9 13.9L14.5 12L11 16.5L8.5 13.5L5 18H13.1C13 18.3 13 18.7 13 19C13 19.7 13.1 20.4 13.3 21Z",this.label||this.hass.localize("ui.components.picture-upload.label"),e,this.supports||this.hass.localize("ui.components.picture-upload.supported_formats"),this._uploading,this._handleFilePicked,this._handleFileCleared)}return(0,p.qy)(w||(w=F`<div class="center-vertical">
      <div class="value">
        <img
          .src=${0}
          alt=${0}
        />
        <div>
          <ha-button
            appearance="plain"
            size="small"
            variant="danger"
            @click=${0}
          >
            ${0}
          </ha-button>
        </div>
      </div>
    </div>`),this.value,this.currentImageAltText||this.hass.localize("ui.components.picture-upload.current_image_alt"),this._handleChangeClick,this.hass.localize("ui.components.picture-upload.clear_picture"))}},{key:"_handleChangeClick",value:function(){this.value=null,(0,h.r)(this,"change")}},{key:"_handleFilePicked",value:(_=(0,o.A)((0,a.A)().m((function e(t){var i;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:i=t.detail.files[0],this.crop?this._cropFile(i):this._uploadFile(i);case 1:return e.a(2)}}),e,this)}))),function(e){return _.apply(this,arguments)})},{key:"_handleFileCleared",value:(u=(0,o.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:this.value=null;case 1:return e.a(2)}}),e,this)}))),function(){return u.apply(this,arguments)})},{key:"_cropFile",value:(d=(0,o.A)((0,a.A)().m((function e(t,i){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(["image/png","image/jpeg","image/gif"].includes(t.type)){e.n=1;break}return(0,f.K$)(this,{text:this.hass.localize("ui.components.picture-upload.unsupported_format")}),e.a(2);case 1:(0,m.Q)(this,{file:t,options:this.cropOptions||{round:!1,aspectRatio:NaN},croppedCallback:e=>{i&&e===t?(this.value=(0,g.Q0)(i,this.size,this.original),(0,h.r)(this,"change")):this._uploadFile(e)}});case 2:return e.a(2)}}),e,this)}))),function(e,t){return d.apply(this,arguments)})},{key:"_uploadFile",value:(i=(0,o.A)((0,a.A)().m((function e(t){var i,o,r,n;return(0,a.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(["image/png","image/jpeg","image/gif"].includes(t.type)){e.n=1;break}return(0,f.K$)(this,{text:this.hass.localize("ui.components.picture-upload.unsupported_format")}),e.a(2);case 1:return this._uploading=!0,e.p=2,e.n=3,(0,g.mF)(this.hass,t);case 3:i=e.v,this.fullMedia?(o={media_content_id:`${g.AP}/${i.id}`,media_content_type:i.content_type,title:i.name,media_class:"image",can_play:!0,can_expand:!1,can_search:!1,thumbnail:(0,g.Q0)(i.id,256)},r=[{},{media_content_type:"app",media_content_id:g.AP}],(0,h.r)(this,"media-picked",{item:o,navigateIds:r})):(this.value=(0,g.Q0)(i.id,this.size,this.original),(0,h.r)(this,"change")),e.n=5;break;case 4:e.p=4,n=e.v,(0,f.K$)(this,{text:n.toString()});case 5:return e.p=5,this._uploading=!1,e.f(5);case 6:return e.a(2)}}),e,this,[[2,4,5,6]])}))),function(e){return i.apply(this,arguments)})}],[{key:"styles",get:function(){return[v.RF,(0,p.AH)(x||(x=F`
        :host {
          display: block;
          height: 240px;
        }
        ha-file-upload {
          height: 100%;
        }
        .center-vertical {
          display: flex;
          align-items: center;
          height: 100%;
        }
        .value {
          width: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        img {
          max-width: 100%;
          max-height: 200px;
          margin-bottom: 4px;
          border-radius: var(--file-upload-image-border-radius);
          transition: opacity 0.3s;
          opacity: var(--picture-opacity, 1);
        }
        img:hover {
          opacity: 1;
        }
      `))]}}]);var i,d,u,_}(p.WF);(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"value",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"label",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"secondary",void 0),(0,d.__decorate)([(0,u.MZ)()],Z.prototype,"supports",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],Z.prototype,"currentImageAltText",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],Z.prototype,"crop",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean,attribute:"select-media"})],Z.prototype,"selectMedia",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean,attribute:"full-media"})],Z.prototype,"fullMedia",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],Z.prototype,"contentIdHelper",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],Z.prototype,"cropOptions",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],Z.prototype,"original",void 0),(0,d.__decorate)([(0,u.MZ)({type:Number})],Z.prototype,"size",void 0),(0,d.__decorate)([(0,u.wk)()],Z.prototype,"_uploading",void 0),Z=(0,d.__decorate)([(0,u.EM)("ha-picture-upload")],Z),t()}catch(z){t(z)}}))},1214:function(e,t,i){i.d(t,{O:function(){return o}});i(23792),i(26099),i(3362),i(62953);var a=i(92542),o=(e,t)=>{(0,a.r)(e,"show-dialog",{dialogTag:"dialog-media-player-browse",dialogImport:()=>Promise.all([i.e("378"),i.e("5633"),i.e("1157"),i.e("9481"),i.e("1283"),i.e("7683")]).then(i.bind(i,47806)),dialogParams:t})}},872:function(e,t,i){i.d(t,{AP:function(){return n},M5:function(){return p},Q0:function(){return s},mF:function(){return c},pD:function(){return l},vS:function(){return d}});var a=i(61397),o=i(50264),r=(i(16280),i(25276),i(26099),i(3362),"/api/image/serve/"),n="media-source://image_upload",l=e=>{var t;if(e.startsWith(r)){var i=(t=e.substring(17)).indexOf("/");i>=0&&(t=t.substring(0,i))}else e.startsWith(n)&&(t=e.substring(n.length+1));return t},s=function(e,t){var i=arguments.length>2&&void 0!==arguments[2]&&arguments[2];if(!i&&!t)throw new Error("Size must be provided if original is false");return i?`/api/image/serve/${e}/original`:`/api/image/serve/${e}/${t}x${t}`},c=function(){var e=(0,o.A)((0,a.A)().m((function e(t,i){var o,r;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return(o=new FormData).append("file",i),e.n=1,t.fetchWithAuth("/api/image/upload",{method:"POST",body:o});case 1:if(413!==(r=e.v).status){e.n=2;break}throw new Error(`Uploaded image is too large (${i.name})`);case 2:if(200===r.status){e.n=3;break}throw new Error("Unknown error");case 3:return e.a(2,r.json())}}),e)})));return function(t,i){return e.apply(this,arguments)}}(),d=(e,t)=>e.callWS({type:"image/delete",image_id:t}),p=function(){var e=(0,o.A)((0,a.A)().m((function e(t,i){var o;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,fetch(t.hassUrl(i));case 1:if((o=e.v).ok){e.n=2;break}throw new Error(`Failed to fetch image: ${o.statusText?o.statusText:o.status}`);case 2:return e.a(2,o.blob())}}),e)})));return function(t,i){return e.apply(this,arguments)}}()},94161:function(e,t,i){i.d(t,{Q:function(){return r}});i(23792),i(26099),i(3362),i(62953);var a=i(92542),o=()=>Promise.all([i.e("3729"),i.e("3566")]).then(i.bind(i,60029)),r=(e,t)=>{(0,a.r)(e,"show-dialog",{dialogTag:"image-cropper-dialog",dialogImport:o,dialogParams:t})}},78436:function(e,t,i){i.d(t,{A:function(){return a}});var a=function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:0,t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;if(0===e)return"0 Bytes";t=t<0?0:t;var i=Math.floor(Math.log(e)/Math.log(1024));return`${parseFloat((e/Math.pow(1024,i)).toFixed(t))} ${["Bytes","KB","MB","GB","TB","PB","EB","ZB","YB"][i]}`}}}]);
//# sourceMappingURL=274.3e703caea8e154ff.js.map