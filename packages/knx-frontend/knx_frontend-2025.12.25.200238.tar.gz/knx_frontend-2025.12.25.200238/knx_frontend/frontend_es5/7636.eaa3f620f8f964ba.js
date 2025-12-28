"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7636"],{48565:function(e,t,a){a.d(t,{d:function(){return i}});var i=e=>{switch(e.language){case"cs":case"de":case"fi":case"fr":case"sk":case"sv":return" ";default:return""}}},485:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(44734),o=a(56038),r=a(69683),n=a(6454),l=a(25460),s=(a(28706),a(23418),a(62062),a(18111),a(61701),a(2892),a(26099),a(62826)),d=a(43306),c=a(96196),u=a(77845),p=a(94333),h=a(92542),v=a(89473),f=(a(60733),a(48565)),_=a(55376),g=a(78436),y=e([d,v]);[d,v]=y.then?(await y)():y;var b,m,$,k,A,w,M,x,Z=e=>e,F="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",B="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M13.5,16V19H10.5V16H8L12,12L16,16H13.5M13,9V3.5L18.5,9H13Z",D=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,o=new Array(a),n=0;n<a;n++)o[n]=arguments[n];return(e=(0,r.A)(this,t,[].concat(o))).multiple=!1,e.disabled=!1,e.uploading=!1,e.autoOpenFileDialog=!1,e._drag=!1,e}return(0,n.A)(t,e),(0,o.A)(t,[{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),this.autoOpenFileDialog&&this._openFilePicker()}},{key:"_name",get:function(){return void 0===this.value?"":"string"==typeof this.value?this.value:(this.value instanceof FileList?Array.from(this.value):(0,_.e)(this.value)).map((e=>e.name)).join(", ")}},{key:"render",value:function(){var e=this.localize||this.hass.localize;return(0,c.qy)(b||(b=Z`
      ${0}
    `),this.uploading?(0,c.qy)(m||(m=Z`<div class="container">
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
          </div>`),this.uploadingLabel||(this.value?e("ui.components.file-upload.uploading_name",{name:this._name}):e("ui.components.file-upload.uploading")),this.progress?(0,c.qy)($||($=Z`<div class="progress">
                    ${0}${0}%
                  </div>`),this.progress,this.hass&&(0,f.d)(this.hass.locale)):c.s6,!this.progress,this.progress?this.progress/100:void 0):(0,c.qy)(k||(k=Z`<label
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
          /></label>`),this.value?"":"input",(0,p.H)({dragged:this._drag,multiple:this.multiple,value:Boolean(this.value)}),this._handleDrop,this._handleDragStart,this._handleDragStart,this._handleDragEnd,this._handleDragEnd,this.value?"string"==typeof this.value?(0,c.qy)(w||(w=Z`<div class="row">
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
                  </div>`),this._openFilePicker,this.icon||B,this.value,this._clearValue,this.deleteLabel||e("ui.common.delete"),F):(this.value instanceof FileList?Array.from(this.value):(0,_.e)(this.value)).map((t=>(0,c.qy)(M||(M=Z`<div class="row">
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
                      </div>`),this._openFilePicker,this.icon||B,t.name,(0,g.A)(t.size),this._clearValue,this.deleteLabel||e("ui.common.delete"),F))):(0,c.qy)(A||(A=Z`<ha-button
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
                  <span class="supports">${0}</span>`),this._openFilePicker,this.icon||B,this.label||e("ui.components.file-upload.label"),this.secondary||e("ui.components.file-upload.secondary"),this.supports),this.accept,this.multiple,this._handleFilePicked))}},{key:"_openFilePicker",value:function(){var e;null===(e=this._input)||void 0===e||e.click()}},{key:"_handleDrop",value:function(e){var t;e.preventDefault(),e.stopPropagation(),null!==(t=e.dataTransfer)&&void 0!==t&&t.files&&(0,h.r)(this,"file-picked",{files:this.multiple||1===e.dataTransfer.files.length?Array.from(e.dataTransfer.files):[e.dataTransfer.files[0]]}),this._drag=!1}},{key:"_handleDragStart",value:function(e){e.preventDefault(),e.stopPropagation(),this._drag=!0}},{key:"_handleDragEnd",value:function(e){e.preventDefault(),e.stopPropagation(),this._drag=!1}},{key:"_handleFilePicked",value:function(e){0!==e.target.files.length&&(this.value=e.target.files,(0,h.r)(this,"file-picked",{files:e.target.files}))}},{key:"_clearValue",value:function(e){e.preventDefault(),this._input.value="",this.value=void 0,(0,h.r)(this,"change"),(0,h.r)(this,"files-cleared")}}])}(c.WF);D.styles=(0,c.AH)(x||(x=Z`
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
  `)),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],D.prototype,"hass",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],D.prototype,"localize",void 0),(0,s.__decorate)([(0,u.MZ)()],D.prototype,"accept",void 0),(0,s.__decorate)([(0,u.MZ)()],D.prototype,"icon",void 0),(0,s.__decorate)([(0,u.MZ)()],D.prototype,"label",void 0),(0,s.__decorate)([(0,u.MZ)()],D.prototype,"secondary",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"uploading-label"})],D.prototype,"uploadingLabel",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"delete-label"})],D.prototype,"deleteLabel",void 0),(0,s.__decorate)([(0,u.MZ)()],D.prototype,"supports",void 0),(0,s.__decorate)([(0,u.MZ)({type:Object})],D.prototype,"value",void 0),(0,s.__decorate)([(0,u.MZ)({type:Boolean})],D.prototype,"multiple",void 0),(0,s.__decorate)([(0,u.MZ)({type:Boolean,reflect:!0})],D.prototype,"disabled",void 0),(0,s.__decorate)([(0,u.MZ)({type:Boolean})],D.prototype,"uploading",void 0),(0,s.__decorate)([(0,u.MZ)({type:Number})],D.prototype,"progress",void 0),(0,s.__decorate)([(0,u.MZ)({type:Boolean,attribute:"auto-open-file-dialog"})],D.prototype,"autoOpenFileDialog",void 0),(0,s.__decorate)([(0,u.wk)()],D.prototype,"_drag",void 0),(0,s.__decorate)([(0,u.P)("#input")],D.prototype,"_input",void 0),D=(0,s.__decorate)([(0,u.EM)("ha-file-upload")],D),t()}catch(H){t(H)}}))},74575:function(e,t,a){a.a(e,(async function(e,i){try{a.r(t),a.d(t,{HaFileSelector:function(){return k}});var o=a(61397),r=a(50264),n=a(44734),l=a(56038),s=a(75864),d=a(69683),c=a(6454),u=a(25460),p=(a(28706),a(62826)),h=a(96196),v=a(77845),f=a(92542),_=a(31169),g=a(10234),y=a(485),b=e([y]);y=(b.then?(await b)():b)[0];var m,$=e=>e,k=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),l=0;l<a;l++)i[l]=arguments[l];return(e=(0,d.A)(this,t,[].concat(i))).disabled=!1,e.required=!0,e._busy=!1,e._removeFile=(0,r.A)((0,o.A)().m((function t(){return(0,o.A)().w((function(t){for(;;)switch(t.p=t.n){case 0:return e._busy=!0,t.p=1,t.n=2,(0,_.n)(e.hass,e.value);case 2:t.n=4;break;case 3:t.p=3,t.v;case 4:return t.p=4,e._busy=!1,t.f(4);case 5:e._filename=void 0,(0,f.r)((0,s.A)(e),"value-changed",{value:""});case 6:return t.a(2)}}),t,null,[[1,3,4,5]])}))),e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){var e,t;return(0,h.qy)(m||(m=$`
      <ha-file-upload
        .hass=${0}
        .accept=${0}
        .icon=${0}
        .label=${0}
        .required=${0}
        .disabled=${0}
        .supports=${0}
        .uploading=${0}
        .value=${0}
        @file-picked=${0}
        @change=${0}
      ></ha-file-upload>
    `),this.hass,null===(e=this.selector.file)||void 0===e?void 0:e.accept,"M13,9V3.5L18.5,9M6,2C4.89,2 4,2.89 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2H6Z",this.label,this.required,this.disabled,this.helper,this._busy,this.value?(null===(t=this._filename)||void 0===t?void 0:t.name)||this.hass.localize("ui.components.selectors.file.unknown_file"):void 0,this._uploadFile,this._removeFile)}},{key:"willUpdate",value:function(e){(0,u.A)(t,"willUpdate",this,3)([e]),e.has("value")&&this._filename&&this.value!==this._filename.fileId&&(this._filename=void 0)}},{key:"_uploadFile",value:(a=(0,r.A)((0,o.A)().m((function e(t){var a,i,r;return(0,o.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this._busy=!0,a=t.detail.files[0],e.p=1,e.n=2,(0,_.Q)(this.hass,a);case 2:i=e.v,this._filename={fileId:i,name:a.name},(0,f.r)(this,"value-changed",{value:i}),e.n=4;break;case 3:e.p=3,r=e.v,(0,g.K$)(this,{text:this.hass.localize("ui.components.selectors.file.upload_failed",{reason:r.message||r})});case 4:return e.p=4,this._busy=!1,e.f(4);case 5:return e.a(2)}}),e,this,[[1,3,4,5]])}))),function(e){return a.apply(this,arguments)})}]);var a}(h.WF);(0,p.__decorate)([(0,v.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,p.__decorate)([(0,v.MZ)({attribute:!1})],k.prototype,"selector",void 0),(0,p.__decorate)([(0,v.MZ)()],k.prototype,"value",void 0),(0,p.__decorate)([(0,v.MZ)()],k.prototype,"label",void 0),(0,p.__decorate)([(0,v.MZ)()],k.prototype,"helper",void 0),(0,p.__decorate)([(0,v.MZ)({type:Boolean})],k.prototype,"disabled",void 0),(0,p.__decorate)([(0,v.MZ)({type:Boolean})],k.prototype,"required",void 0),(0,p.__decorate)([(0,v.wk)()],k.prototype,"_filename",void 0),(0,p.__decorate)([(0,v.wk)()],k.prototype,"_busy",void 0),k=(0,p.__decorate)([(0,v.EM)("ha-selector-file")],k),i()}catch(A){i(A)}}))},31169:function(e,t,a){a.d(t,{Q:function(){return r},n:function(){return n}});var i=a(61397),o=a(50264),r=(a(16280),function(){var e=(0,o.A)((0,i.A)().m((function e(t,a){var o,r,n;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:return(o=new FormData).append("file",a),e.n=1,t.fetchWithAuth("/api/file_upload",{method:"POST",body:o});case 1:if(413!==(r=e.v).status){e.n=2;break}throw new Error(`Uploaded file is too large (${a.name})`);case 2:if(200===r.status){e.n=3;break}throw new Error("Unknown error");case 3:return e.n=4,r.json();case 4:return n=e.v,e.a(2,n.file_id)}}),e)})));return function(t,a){return e.apply(this,arguments)}}()),n=function(){var e=(0,o.A)((0,i.A)().m((function e(t,a){return(0,i.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.callApi("DELETE","file_upload",{file_id:a}))}),e)})));return function(t,a){return e.apply(this,arguments)}}()},78436:function(e,t,a){a.d(t,{A:function(){return i}});var i=function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:0,t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;if(0===e)return"0 Bytes";t=t<0?0:t;var a=Math.floor(Math.log(e)/Math.log(1024));return`${parseFloat((e/Math.pow(1024,a)).toFixed(t))} ${["Bytes","KB","MB","GB","TB","PB","EB","ZB","YB"][a]}`}}}]);
//# sourceMappingURL=7636.eaa3f620f8f964ba.js.map