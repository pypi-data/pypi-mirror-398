export const __webpack_id__="6133";export const __webpack_ids__=["6133"];export const __webpack_modules__={48565:function(t,e,o){o.d(e,{d:()=>a});const a=t=>{switch(t.language){case"cs":case"de":case"fi":case"fr":case"sk":case"sv":return" ";default:return""}}},485:function(t,e,o){o.a(t,(async function(t,e){try{var a=o(62826),i=(o(63687),o(96196)),r=o(77845),n=o(94333),s=o(92542),l=o(89473),d=(o(60733),o(48565)),c=o(55376),p=o(78436),h=t([l]);l=(h.then?(await h)():h)[0];const v="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",u="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M13.5,16V19H10.5V16H8L12,12L16,16H13.5M13,9V3.5L18.5,9H13Z";class b extends i.WF{firstUpdated(t){super.firstUpdated(t),this.autoOpenFileDialog&&this._openFilePicker()}get _name(){if(void 0===this.value)return"";if("string"==typeof this.value)return this.value;return(this.value instanceof FileList?Array.from(this.value):(0,c.e)(this.value)).map((t=>t.name)).join(", ")}render(){const t=this.localize||this.hass.localize;return i.qy`
      ${this.uploading?i.qy`<div class="container">
            <div class="uploading">
              <span class="header"
                >${this.uploadingLabel||(this.value?t("ui.components.file-upload.uploading_name",{name:this._name}):t("ui.components.file-upload.uploading"))}</span
              >
              ${this.progress?i.qy`<div class="progress">
                    ${this.progress}${this.hass&&(0,d.d)(this.hass.locale)}%
                  </div>`:i.s6}
            </div>
            <mwc-linear-progress
              .indeterminate=${!this.progress}
              .progress=${this.progress?this.progress/100:void 0}
            ></mwc-linear-progress>
          </div>`:i.qy`<label
            for=${this.value?"":"input"}
            class="container ${(0,n.H)({dragged:this._drag,multiple:this.multiple,value:Boolean(this.value)})}"
            @drop=${this._handleDrop}
            @dragenter=${this._handleDragStart}
            @dragover=${this._handleDragStart}
            @dragleave=${this._handleDragEnd}
            @dragend=${this._handleDragEnd}
            >${this.value?"string"==typeof this.value?i.qy`<div class="row">
                    <div class="value" @click=${this._openFilePicker}>
                      <ha-svg-icon
                        .path=${this.icon||u}
                      ></ha-svg-icon>
                      ${this.value}
                    </div>
                    <ha-icon-button
                      @click=${this._clearValue}
                      .label=${this.deleteLabel||t("ui.common.delete")}
                      .path=${v}
                    ></ha-icon-button>
                  </div>`:(this.value instanceof FileList?Array.from(this.value):(0,c.e)(this.value)).map((e=>i.qy`<div class="row">
                        <div class="value" @click=${this._openFilePicker}>
                          <ha-svg-icon
                            .path=${this.icon||u}
                          ></ha-svg-icon>
                          ${e.name} - ${(0,p.A)(e.size)}
                        </div>
                        <ha-icon-button
                          @click=${this._clearValue}
                          .label=${this.deleteLabel||t("ui.common.delete")}
                          .path=${v}
                        ></ha-icon-button>
                      </div>`)):i.qy`<ha-button
                    size="small"
                    appearance="filled"
                    @click=${this._openFilePicker}
                  >
                    <ha-svg-icon
                      slot="start"
                      .path=${this.icon||u}
                    ></ha-svg-icon>
                    ${this.label||t("ui.components.file-upload.label")}
                  </ha-button>
                  <span class="secondary"
                    >${this.secondary||t("ui.components.file-upload.secondary")}</span
                  >
                  <span class="supports">${this.supports}</span>`}
            <input
              id="input"
              type="file"
              class="file"
              .accept=${this.accept}
              .multiple=${this.multiple}
              @change=${this._handleFilePicked}
          /></label>`}
    `}_openFilePicker(){this._input?.click()}_handleDrop(t){t.preventDefault(),t.stopPropagation(),t.dataTransfer?.files&&(0,s.r)(this,"file-picked",{files:this.multiple||1===t.dataTransfer.files.length?Array.from(t.dataTransfer.files):[t.dataTransfer.files[0]]}),this._drag=!1}_handleDragStart(t){t.preventDefault(),t.stopPropagation(),this._drag=!0}_handleDragEnd(t){t.preventDefault(),t.stopPropagation(),this._drag=!1}_handleFilePicked(t){0!==t.target.files.length&&(this.value=t.target.files,(0,s.r)(this,"file-picked",{files:t.target.files}))}_clearValue(t){t.preventDefault(),this._input.value="",this.value=void 0,(0,s.r)(this,"change"),(0,s.r)(this,"files-cleared")}constructor(...t){super(...t),this.multiple=!1,this.disabled=!1,this.uploading=!1,this.autoOpenFileDialog=!1,this._drag=!1}}b.styles=i.AH`
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
  `,(0,a.__decorate)([(0,r.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],b.prototype,"localize",void 0),(0,a.__decorate)([(0,r.MZ)()],b.prototype,"accept",void 0),(0,a.__decorate)([(0,r.MZ)()],b.prototype,"icon",void 0),(0,a.__decorate)([(0,r.MZ)()],b.prototype,"label",void 0),(0,a.__decorate)([(0,r.MZ)()],b.prototype,"secondary",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:"uploading-label"})],b.prototype,"uploadingLabel",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:"delete-label"})],b.prototype,"deleteLabel",void 0),(0,a.__decorate)([(0,r.MZ)()],b.prototype,"supports",void 0),(0,a.__decorate)([(0,r.MZ)({type:Object})],b.prototype,"value",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],b.prototype,"multiple",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],b.prototype,"disabled",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],b.prototype,"uploading",void 0),(0,a.__decorate)([(0,r.MZ)({type:Number})],b.prototype,"progress",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,attribute:"auto-open-file-dialog"})],b.prototype,"autoOpenFileDialog",void 0),(0,a.__decorate)([(0,r.wk)()],b.prototype,"_drag",void 0),(0,a.__decorate)([(0,r.P)("#input")],b.prototype,"_input",void 0),b=(0,a.__decorate)([(0,r.EM)("ha-file-upload")],b),e()}catch(v){e(v)}}))},31169:function(t,e,o){o.d(e,{Q:()=>a,n:()=>i});const a=async(t,e)=>{const o=new FormData;o.append("file",e);const a=await t.fetchWithAuth("/api/file_upload",{method:"POST",body:o});if(413===a.status)throw new Error(`Uploaded file is too large (${e.name})`);if(200!==a.status)throw new Error("Unknown error");return(await a.json()).file_id},i=async(t,e)=>t.callApi("DELETE","file_upload",{file_id:e})},95260:function(t,e,o){o.d(e,{PS:()=>a,VR:()=>i});const a=t=>t.data,i=t=>"object"==typeof t?"object"==typeof t.body?t.body.message||"Unknown error, see supervisor logs":t.body||t.message||"Unknown error, see supervisor logs":t;new Set([502,503,504])},10234:function(t,e,o){o.d(e,{K$:()=>n,an:()=>l,dk:()=>s});var a=o(92542);const i=()=>Promise.all([o.e("6009"),o.e("5791"),o.e("5463")]).then(o.bind(o,22316)),r=(t,e,o)=>new Promise((r=>{const n=e.cancel,s=e.confirm;(0,a.r)(t,"show-dialog",{dialogTag:"dialog-box",dialogImport:i,dialogParams:{...e,...o,cancel:()=>{r(!!o?.prompt&&null),n&&n()},confirm:t=>{r(!o?.prompt||t),s&&s(t)}}})})),n=(t,e)=>r(t,e),s=(t,e)=>r(t,e,{confirmation:!0}),l=(t,e)=>r(t,e,{prompt:!0})},84884:function(t,e,o){var a=o(62826),i=o(96196),r=o(77845),n=o(94333),s=o(22786),l=o(55376),d=o(92209);const c=(t,e)=>!e.component||(0,l.e)(e.component).some((e=>(0,d.x)(t,e))),p=(t,e)=>!e.not_component||!(0,l.e)(e.not_component).some((e=>(0,d.x)(t,e))),h=t=>t.core,v=(t,e)=>(t=>t.advancedOnly)(e)&&!(t=>t.userData?.showAdvanced)(t);var u=o(5871),b=o(39501),f=(o(371),o(45397),o(60961),o(32288));o(95591);class g extends i.WF{render(){return i.qy`
      <div
        tabindex="0"
        role="tab"
        aria-selected=${this.active}
        aria-label=${(0,f.J)(this.name)}
        @keydown=${this._handleKeyDown}
      >
        ${this.narrow?i.qy`<slot name="icon"></slot>`:""}
        <span class="name">${this.name}</span>
        <ha-ripple></ha-ripple>
      </div>
    `}_handleKeyDown(t){"Enter"===t.key&&t.target.click()}constructor(...t){super(...t),this.active=!1,this.narrow=!1}}g.styles=i.AH`
    div {
      padding: 0 32px;
      display: flex;
      flex-direction: column;
      text-align: center;
      box-sizing: border-box;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: var(--header-height);
      cursor: pointer;
      position: relative;
      outline: none;
    }

    .name {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
    }

    :host([active]) {
      color: var(--primary-color);
    }

    :host(:not([narrow])[active]) div {
      border-bottom: 2px solid var(--primary-color);
    }

    :host([narrow]) {
      min-width: 0;
      display: flex;
      justify-content: center;
      overflow: hidden;
    }

    :host([narrow]) div {
      padding: 0 4px;
    }

    div:focus-visible:before {
      position: absolute;
      display: block;
      content: "";
      inset: 0;
      background-color: var(--secondary-text-color);
      opacity: 0.08;
    }
  `,(0,a.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],g.prototype,"active",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],g.prototype,"narrow",void 0),(0,a.__decorate)([(0,r.MZ)()],g.prototype,"name",void 0),g=(0,a.__decorate)([(0,r.EM)("ha-tab")],g);var x=o(39396);class _ extends i.WF{willUpdate(t){t.has("route")&&(this._activeTab=this.tabs.find((t=>`${this.route.prefix}${this.route.path}`.includes(t.path)))),super.willUpdate(t)}render(){const t=this._getTabs(this.tabs,this._activeTab,this.hass.config.components,this.hass.language,this.hass.userData,this.narrow,this.localizeFunc||this.hass.localize),e=t.length>1;return i.qy`
      <div class="toolbar">
        <slot name="toolbar">
          <div class="toolbar-content">
            ${this.mainPage||!this.backPath&&history.state?.root?i.qy`
                  <ha-menu-button
                    .hassio=${this.supervisor}
                    .hass=${this.hass}
                    .narrow=${this.narrow}
                  ></ha-menu-button>
                `:this.backPath?i.qy`
                    <a href=${this.backPath}>
                      <ha-icon-button-arrow-prev
                        .hass=${this.hass}
                      ></ha-icon-button-arrow-prev>
                    </a>
                  `:i.qy`
                    <ha-icon-button-arrow-prev
                      .hass=${this.hass}
                      @click=${this._backTapped}
                    ></ha-icon-button-arrow-prev>
                  `}
            ${this.narrow||!e?i.qy`<div class="main-title">
                  <slot name="header">${e?"":t[0]}</slot>
                </div>`:""}
            ${e&&!this.narrow?i.qy`<div id="tabbar">${t}</div>`:""}
            <div id="toolbar-icon">
              <slot name="toolbar-icon"></slot>
            </div>
          </div>
        </slot>
        ${e&&this.narrow?i.qy`<div id="tabbar" class="bottom-bar">${t}</div>`:""}
      </div>
      <div
        class=${(0,n.H)({container:!0,tabs:e&&this.narrow})}
      >
        ${this.pane?i.qy`<div class="pane">
              <div class="shadow-container"></div>
              <div class="ha-scrollbar">
                <slot name="pane"></slot>
              </div>
            </div>`:i.s6}
        <div
          class="content ha-scrollbar ${(0,n.H)({tabs:e})}"
          @scroll=${this._saveScrollPos}
        >
          <slot></slot>
          ${this.hasFab?i.qy`<div class="fab-bottom-space"></div>`:i.s6}
        </div>
      </div>
      <div id="fab" class=${(0,n.H)({tabs:e})}>
        <slot name="fab"></slot>
      </div>
    `}_saveScrollPos(t){this._savedScrollPos=t.target.scrollTop}_backTapped(){this.backCallback?this.backCallback():(0,u.O)()}static get styles(){return[x.dp,i.AH`
        :host {
          display: block;
          height: 100%;
          background-color: var(--primary-background-color);
        }

        :host([narrow]) {
          width: 100%;
          position: fixed;
        }

        .container {
          display: flex;
          height: calc(
            100% - var(--header-height, 0px) - var(--safe-area-inset-top, 0px)
          );
        }

        ha-menu-button {
          margin-right: 24px;
          margin-inline-end: 24px;
          margin-inline-start: initial;
        }

        .toolbar {
          font-size: var(--ha-font-size-xl);
          height: calc(
            var(--header-height, 0px) + var(--safe-area-inset-top, 0px)
          );
          padding-top: var(--safe-area-inset-top);
          padding-right: var(--safe-area-inset-right);
          background-color: var(--sidebar-background-color);
          font-weight: var(--ha-font-weight-normal);
          border-bottom: 1px solid var(--divider-color);
          box-sizing: border-box;
        }
        :host([narrow]) .toolbar {
          padding-left: var(--safe-area-inset-left);
        }
        .toolbar-content {
          padding: 8px 12px;
          display: flex;
          align-items: center;
          height: 100%;
          box-sizing: border-box;
        }
        :host([narrow]) .toolbar-content {
          padding: 4px;
        }
        .toolbar a {
          color: var(--sidebar-text-color);
          text-decoration: none;
        }
        .bottom-bar a {
          width: 25%;
        }

        #tabbar {
          display: flex;
          font-size: var(--ha-font-size-m);
          overflow: hidden;
        }

        #tabbar > a {
          overflow: hidden;
          max-width: 45%;
        }

        #tabbar.bottom-bar {
          position: absolute;
          bottom: 0;
          left: 0;
          padding: 0 16px;
          box-sizing: border-box;
          background-color: var(--sidebar-background-color);
          border-top: 1px solid var(--divider-color);
          justify-content: space-around;
          z-index: 2;
          font-size: var(--ha-font-size-s);
          width: 100%;
          padding-bottom: var(--safe-area-inset-bottom);
        }

        #tabbar:not(.bottom-bar) {
          flex: 1;
          justify-content: center;
        }

        :host(:not([narrow])) #toolbar-icon {
          min-width: 40px;
        }

        ha-menu-button,
        ha-icon-button-arrow-prev,
        ::slotted([slot="toolbar-icon"]) {
          display: flex;
          flex-shrink: 0;
          pointer-events: auto;
          color: var(--sidebar-icon-color);
        }

        .main-title {
          flex: 1;
          max-height: var(--header-height);
          line-height: var(--ha-line-height-normal);
          color: var(--sidebar-text-color);
          margin: var(--main-title-margin, var(--margin-title));
        }

        .content {
          position: relative;
          width: 100%;
          margin-right: var(--safe-area-inset-right);
          margin-inline-end: var(--safe-area-inset-right);
          margin-bottom: var(--safe-area-inset-bottom);
          overflow: auto;
          -webkit-overflow-scrolling: touch;
        }
        :host([narrow]) .content {
          margin-left: var(--safe-area-inset-left);
          margin-inline-start: var(--safe-area-inset-left);
        }
        :host([narrow]) .content.tabs {
          /* Bottom bar reuses header height */
          margin-bottom: calc(
            var(--header-height, 0px) + var(--safe-area-inset-bottom, 0px)
          );
        }

        .content .fab-bottom-space {
          height: calc(64px + var(--safe-area-inset-bottom, 0px));
        }

        :host([narrow]) .content.tabs .fab-bottom-space {
          height: calc(80px + var(--safe-area-inset-bottom, 0px));
        }

        #fab {
          position: fixed;
          right: calc(16px + var(--safe-area-inset-right, 0px));
          inset-inline-end: calc(16px + var(--safe-area-inset-right));
          inset-inline-start: initial;
          bottom: calc(16px + var(--safe-area-inset-bottom, 0px));
          z-index: 1;
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: var(--ha-space-2);
        }
        :host([narrow]) #fab.tabs {
          bottom: calc(84px + var(--safe-area-inset-bottom, 0px));
        }
        #fab[is-wide] {
          bottom: 24px;
          right: 24px;
          inset-inline-end: 24px;
          inset-inline-start: initial;
        }

        .pane {
          border-right: 1px solid var(--divider-color);
          border-inline-end: 1px solid var(--divider-color);
          border-inline-start: initial;
          box-sizing: border-box;
          display: flex;
          flex: 0 0 var(--sidepane-width, 250px);
          width: var(--sidepane-width, 250px);
          flex-direction: column;
          position: relative;
        }
        .pane .ha-scrollbar {
          flex: 1;
        }
      `]}constructor(...t){super(...t),this.supervisor=!1,this.mainPage=!1,this.narrow=!1,this.isWide=!1,this.pane=!1,this.hasFab=!1,this._getTabs=(0,s.A)(((t,e,o,a,r,n,s)=>{const l=t.filter((t=>((t,e)=>(h(e)||c(t,e))&&!v(t,e)&&p(t,e))(this.hass,t)));if(l.length<2){if(1===l.length){const t=l[0];return[t.translationKey?s(t.translationKey):t.name]}return[""]}return l.map((t=>i.qy`
          <a href=${t.path}>
            <ha-tab
              .hass=${this.hass}
              .active=${t.path===e?.path}
              .narrow=${this.narrow}
              .name=${t.translationKey?s(t.translationKey):t.name}
            >
              ${t.iconPath?i.qy`<ha-svg-icon
                    slot="icon"
                    .path=${t.iconPath}
                  ></ha-svg-icon>`:""}
            </ha-tab>
          </a>
        `))}))}}(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"supervisor",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"localizeFunc",void 0),(0,a.__decorate)([(0,r.MZ)({type:String,attribute:"back-path"})],_.prototype,"backPath",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"backCallback",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,attribute:"main-page"})],_.prototype,"mainPage",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"route",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:!1})],_.prototype,"tabs",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0})],_.prototype,"narrow",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,reflect:!0,attribute:"is-wide"})],_.prototype,"isWide",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],_.prototype,"pane",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean,attribute:"has-fab"})],_.prototype,"hasFab",void 0),(0,a.__decorate)([(0,r.wk)()],_.prototype,"_activeTab",void 0),(0,a.__decorate)([(0,b.a)(".content")],_.prototype,"_savedScrollPos",void 0),(0,a.__decorate)([(0,r.Ls)({passive:!0})],_.prototype,"_saveScrollPos",null),_=(0,a.__decorate)([(0,r.EM)("hass-tabs-subpage")],_)},78436:function(t,e,o){o.d(e,{A:()=>a});const a=(t=0,e=2)=>{if(0===t)return"0 Bytes";e=e<0?0:e;const o=Math.floor(Math.log(t)/Math.log(1024));return`${parseFloat((t/1024**o).toFixed(e))} ${["Bytes","KB","MB","GB","TB","PB","EB","ZB","YB"][o]}`}},6431:function(t,e,o){o.d(e,{x:()=>a});const a="2025.12.25.200238"},45812:function(t,e,o){o.a(t,(async function(t,a){try{o.r(e),o.d(e,{KNXInfo:()=>m});var i=o(62826),r=o(96196),n=o(77845),s=o(92542),l=(o(95379),o(84884),o(89473)),d=o(485),c=o(81774),p=o(31169),h=o(95260),v=o(10234),u=o(65294),b=o(78577),f=o(6431),g=t([l,d,c]);[l,d,c]=g.then?(await g)():g;const x="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M13.5,16V19H10.5V16H8L12,12L16,16H13.5M13,9V3.5L18.5,9H13Z",_=new b.Q("info");class m extends r.WF{render(){return r.qy`
      <hass-tabs-subpage
        .hass=${this.hass}
        .narrow=${this.narrow}
        .route=${this.route}
        .tabs=${this.tabs}
        .localizeFunc=${this.knx.localize}
        main-page
      >
        <div class="columns">
          ${this._renderInfoCard()}
          ${this.knx.projectInfo?this._renderProjectDataCard(this.knx.projectInfo):r.s6}
          ${this._renderProjectUploadCard()}
        </div>
      </hass-tabs-subpage>
    `}_renderInfoCard(){return r.qy` <ha-card class="knx-info">
      <div class="card-content knx-info-section">
        <div class="knx-content-row header">${this.knx.localize("info_information_header")}</div>

        <div class="knx-content-row">
          <div>XKNX Version</div>
          <div>${this.knx.connectionInfo.version}</div>
        </div>

        <div class="knx-content-row">
          <div>KNX-Frontend Version</div>
          <div>${f.x}</div>
        </div>

        <div class="knx-content-row">
          <div>${this.knx.localize("info_connected_to_bus")}</div>
          <div>
            ${this.hass.localize(this.knx.connectionInfo.connected?"ui.common.yes":"ui.common.no")}
          </div>
        </div>

        <div class="knx-content-row">
          <div>${this.knx.localize("info_individual_address")}</div>
          <div>${this.knx.connectionInfo.current_address}</div>
        </div>

        <div class="knx-bug-report">
          ${this.knx.localize("info_issue_tracker")}
          <a href="https://github.com/XKNX/knx-integration" target="_blank">xknx/knx-integration</a>
        </div>

        <div class="knx-bug-report">
          ${this.knx.localize("info_my_knx")}
          <a href="https://my.knx.org" target="_blank">my.knx.org</a>
        </div>
      </div>
    </ha-card>`}_renderProjectDataCard(t){return r.qy`
      <ha-card class="knx-info">
          <div class="card-content knx-content">
            <div class="header knx-content-row">
              ${this.knx.localize("info_project_data_header")}
            </div>
            <div class="knx-content-row">
              <div>${this.knx.localize("info_project_data_name")}</div>
              <div>${t.name}</div>
            </div>
            <div class="knx-content-row">
              <div>${this.knx.localize("info_project_data_last_modified")}</div>
              <div>${new Date(t.last_modified).toUTCString()}</div>
            </div>
            <div class="knx-content-row">
              <div>${this.knx.localize("info_project_data_tool_version")}</div>
              <div>${t.tool_version}</div>
            </div>
            <div class="knx-content-row">
              <div>${this.knx.localize("info_project_data_xknxproject_version")}</div>
              <div>${t.xknxproject_version}</div>
            </div>
            <div class="knx-button-row">
              <ha-button
                class="knx-warning push-right"
                @click=${this._removeProject}
                .disabled=${this._uploading||!this.knx.projectInfo}
                >
                ${this.knx.localize("info_project_delete")}
              </ha-button>
            </div>
          </div>
        </div>
      </ha-card>
    `}_renderProjectUploadCard(){return r.qy` <ha-card class="knx-info">
      <div class="card-content knx-content">
        <div class="knx-content-row header">${this.knx.localize("info_project_file_header")}</div>
        <div class="knx-content-row">${this.knx.localize("info_project_upload_description")}</div>
        <div class="knx-content-row">
          <ha-file-upload
            .hass=${this.hass}
            accept=".knxproj, .knxprojarchive"
            .icon=${x}
            .label=${this.knx.localize("info_project_file")}
            .value=${this._projectFile?.name}
            .uploading=${this._uploading}
            @file-picked=${this._filePicked}
          ></ha-file-upload>
        </div>
        <div class="knx-content-row">
          <ha-selector-text
            .hass=${this.hass}
            .value=${this._projectPassword||""}
            .label=${this.hass.localize("ui.login-form.password")}
            .selector=${{text:{multiline:!1,type:"password"}}}
            .required=${!1}
            @value-changed=${this._passwordChanged}
          >
          </ha-selector-text>
        </div>
        <div class="knx-button-row">
          <ha-button
            class="push-right"
            @click=${this._uploadFile}
            .disabled=${this._uploading||!this._projectFile}
            >${this.hass.localize("ui.common.submit")}</ha-button
          >
        </div>
      </div>
    </ha-card>`}_filePicked(t){this._projectFile=t.detail.files[0]}_passwordChanged(t){this._projectPassword=t.detail.value}async _uploadFile(t){const e=this._projectFile;if(void 0===e)return;let o;this._uploading=!0;try{const t=await(0,p.Q)(this.hass,e);await(0,u.dc)(this.hass,t,this._projectPassword||"")}catch(a){o=a,(0,v.K$)(this,{title:"Upload failed",text:(0,h.VR)(a)})}finally{o||(this._projectFile=void 0,this._projectPassword=void 0),this._uploading=!1,(0,s.r)(this,"knx-reload")}}async _removeProject(t){if(await(0,v.dk)(this,{text:this.knx.localize("info_project_delete")}))try{await(0,u.gV)(this.hass)}catch(e){(0,v.K$)(this,{title:"Deletion failed",text:(0,h.VR)(e)})}finally{(0,s.r)(this,"knx-reload")}else _.debug("User cancelled deletion")}constructor(...t){super(...t),this._uploading=!1}}m.styles=r.AH`
    .columns {
      display: flex;
      justify-content: center;
    }

    @media screen and (max-width: 1232px) {
      .columns {
        flex-direction: column;
      }

      .knx-button-row {
        margin-top: 20px;
      }

      .knx-info {
        margin-right: 8px;
      }
    }

    @media screen and (min-width: 1233px) {
      .knx-button-row {
        margin-top: auto;
      }

      .knx-info {
        width: 400px;
      }
    }

    .knx-info {
      margin-left: 8px;
      margin-top: 8px;
    }

    .knx-content {
      display: flex;
      flex-direction: column;
      height: 100%;
      box-sizing: border-box;
    }

    .knx-content-row {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
    }

    .knx-content-row > div:nth-child(2) {
      margin-left: 1rem;
    }

    .knx-button-row {
      display: flex;
      flex-direction: row;
      vertical-align: bottom;
      padding-top: 16px;
    }

    .push-left {
      margin-right: auto;
    }

    .push-right {
      margin-left: auto;
    }

    .knx-warning {
      --mdc-theme-primary: var(--error-color);
    }

    .knx-project-description {
      margin-top: -8px;
      padding: 0px 16px 16px;
    }

    .knx-delete-project-button {
      position: absolute;
      bottom: 0;
      right: 0;
    }

    .knx-bug-report {
      margin-top: 20px;

      a {
        text-decoration: none;
      }
    }

    .header {
      color: var(--ha-card-header-color, --primary-text-color);
      font-family: var(--ha-card-header-font-family, inherit);
      font-size: var(--ha-card-header-font-size, 24px);
      letter-spacing: -0.012em;
      line-height: 48px;
      padding: -4px 16px 16px;
      display: inline-block;
      margin-block-start: 0px;
      margin-block-end: 4px;
      font-weight: normal;
    }

    ha-file-upload,
    ha-selector-text {
      width: 100%;
      margin-top: 8px;
    }
  `,(0,i.__decorate)([(0,n.MZ)({type:Object})],m.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],m.prototype,"knx",void 0),(0,i.__decorate)([(0,n.MZ)({type:Boolean,reflect:!0})],m.prototype,"narrow",void 0),(0,i.__decorate)([(0,n.MZ)({type:Object})],m.prototype,"route",void 0),(0,i.__decorate)([(0,n.MZ)({type:Array,reflect:!1})],m.prototype,"tabs",void 0),(0,i.__decorate)([(0,n.wk)()],m.prototype,"_projectPassword",void 0),(0,i.__decorate)([(0,n.wk)()],m.prototype,"_uploading",void 0),(0,i.__decorate)([(0,n.wk)()],m.prototype,"_projectFile",void 0),m=(0,i.__decorate)([(0,n.EM)("knx-info")],m),a()}catch(x){a(x)}}))}};
//# sourceMappingURL=6133.2bdfb49e00f21c26.js.map