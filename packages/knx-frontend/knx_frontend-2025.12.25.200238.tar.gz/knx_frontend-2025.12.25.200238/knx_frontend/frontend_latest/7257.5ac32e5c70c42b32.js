export const __webpack_id__="7257";export const __webpack_ids__=["7257"];export const __webpack_modules__={17963:function(o,t,a){a.r(t);var r=a(62826),e=a(96196),i=a(77845),n=a(94333),l=a(92542);a(60733),a(60961);const s={info:"M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",warning:"M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",error:"M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z",success:"M20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4C12.76,4 13.5,4.11 14.2,4.31L15.77,2.74C14.61,2.26 13.34,2 12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"};class c extends e.WF{render(){return e.qy`
      <div
        class="issue-type ${(0,n.H)({[this.alertType]:!0})}"
        role="alert"
      >
        <div class="icon ${this.title?"":"no-title"}">
          <slot name="icon">
            <ha-svg-icon .path=${s[this.alertType]}></ha-svg-icon>
          </slot>
        </div>
        <div class=${(0,n.H)({content:!0,narrow:this.narrow})}>
          <div class="main-content">
            ${this.title?e.qy`<div class="title">${this.title}</div>`:e.s6}
            <slot></slot>
          </div>
          <div class="action">
            <slot name="action">
              ${this.dismissable?e.qy`<ha-icon-button
                    @click=${this._dismissClicked}
                    label="Dismiss alert"
                    .path=${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"}
                  ></ha-icon-button>`:e.s6}
            </slot>
          </div>
        </div>
      </div>
    `}_dismissClicked(){(0,l.r)(this,"alert-dismissed-clicked")}constructor(...o){super(...o),this.title="",this.alertType="info",this.dismissable=!1,this.narrow=!1}}c.styles=e.AH`
    .issue-type {
      position: relative;
      padding: 8px;
      display: flex;
    }
    .icon {
      height: var(--ha-alert-icon-size, 24px);
      width: var(--ha-alert-icon-size, 24px);
    }
    .issue-type::after {
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      opacity: 0.12;
      pointer-events: none;
      content: "";
      border-radius: var(--ha-border-radius-sm);
    }
    .icon.no-title {
      align-self: center;
    }
    .content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      text-align: var(--float-start);
    }
    .content.narrow {
      flex-direction: column;
      align-items: flex-end;
    }
    .action {
      z-index: 1;
      width: min-content;
      --mdc-theme-primary: var(--primary-text-color);
    }
    .main-content {
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: normal;
      margin-left: 8px;
      margin-right: 0;
      margin-inline-start: 8px;
      margin-inline-end: 8px;
    }
    .title {
      margin-top: 2px;
      font-weight: var(--ha-font-weight-bold);
    }
    .action ha-icon-button {
      --mdc-theme-primary: var(--primary-text-color);
      --mdc-icon-button-size: 36px;
    }
    .issue-type.info > .icon {
      color: var(--info-color);
    }
    .issue-type.info::after {
      background-color: var(--info-color);
    }

    .issue-type.warning > .icon {
      color: var(--warning-color);
    }
    .issue-type.warning::after {
      background-color: var(--warning-color);
    }

    .issue-type.error > .icon {
      color: var(--error-color);
    }
    .issue-type.error::after {
      background-color: var(--error-color);
    }

    .issue-type.success > .icon {
      color: var(--success-color);
    }
    .issue-type.success::after {
      background-color: var(--success-color);
    }
    :host ::slotted(ul) {
      margin: 0;
      padding-inline-start: 20px;
    }
  `,(0,r.__decorate)([(0,i.MZ)()],c.prototype,"title",void 0),(0,r.__decorate)([(0,i.MZ)({attribute:"alert-type"})],c.prototype,"alertType",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean})],c.prototype,"dismissable",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean})],c.prototype,"narrow",void 0),c=(0,r.__decorate)([(0,i.EM)("ha-alert")],c)},89473:function(o,t,a){a.a(o,(async function(o,t){try{var r=a(62826),e=a(88496),i=a(96196),n=a(77845),l=o([e]);e=(l.then?(await l)():l)[0];class s extends e.A{static get styles(){return[e.A.styles,i.AH`
        :host {
          --wa-form-control-padding-inline: 16px;
          --wa-font-weight-action: var(--ha-font-weight-medium);
          --wa-form-control-border-radius: var(
            --ha-button-border-radius,
            var(--ha-border-radius-pill)
          );

          --wa-form-control-height: var(
            --ha-button-height,
            var(--button-height, 40px)
          );
        }
        .button {
          font-size: var(--ha-font-size-m);
          line-height: 1;

          transition: background-color 0.15s ease-in-out;
          text-wrap: wrap;
        }

        :host([size="small"]) .button {
          --wa-form-control-height: var(
            --ha-button-height,
            var(--button-height, 32px)
          );
          font-size: var(--wa-font-size-s, var(--ha-font-size-m));
          --wa-form-control-padding-inline: 12px;
        }

        :host([variant="brand"]) {
          --button-color-fill-normal-active: var(
            --ha-color-fill-primary-normal-active
          );
          --button-color-fill-normal-hover: var(
            --ha-color-fill-primary-normal-hover
          );
          --button-color-fill-loud-active: var(
            --ha-color-fill-primary-loud-active
          );
          --button-color-fill-loud-hover: var(
            --ha-color-fill-primary-loud-hover
          );
        }

        :host([variant="neutral"]) {
          --button-color-fill-normal-active: var(
            --ha-color-fill-neutral-normal-active
          );
          --button-color-fill-normal-hover: var(
            --ha-color-fill-neutral-normal-hover
          );
          --button-color-fill-loud-active: var(
            --ha-color-fill-neutral-loud-active
          );
          --button-color-fill-loud-hover: var(
            --ha-color-fill-neutral-loud-hover
          );
        }

        :host([variant="success"]) {
          --button-color-fill-normal-active: var(
            --ha-color-fill-success-normal-active
          );
          --button-color-fill-normal-hover: var(
            --ha-color-fill-success-normal-hover
          );
          --button-color-fill-loud-active: var(
            --ha-color-fill-success-loud-active
          );
          --button-color-fill-loud-hover: var(
            --ha-color-fill-success-loud-hover
          );
        }

        :host([variant="warning"]) {
          --button-color-fill-normal-active: var(
            --ha-color-fill-warning-normal-active
          );
          --button-color-fill-normal-hover: var(
            --ha-color-fill-warning-normal-hover
          );
          --button-color-fill-loud-active: var(
            --ha-color-fill-warning-loud-active
          );
          --button-color-fill-loud-hover: var(
            --ha-color-fill-warning-loud-hover
          );
        }

        :host([variant="danger"]) {
          --button-color-fill-normal-active: var(
            --ha-color-fill-danger-normal-active
          );
          --button-color-fill-normal-hover: var(
            --ha-color-fill-danger-normal-hover
          );
          --button-color-fill-loud-active: var(
            --ha-color-fill-danger-loud-active
          );
          --button-color-fill-loud-hover: var(
            --ha-color-fill-danger-loud-hover
          );
        }

        :host([appearance~="plain"]) .button {
          color: var(--wa-color-on-normal);
          background-color: transparent;
        }
        :host([appearance~="plain"]) .button.disabled {
          background-color: transparent;
          color: var(--ha-color-on-disabled-quiet);
        }

        :host([appearance~="outlined"]) .button.disabled {
          background-color: transparent;
          color: var(--ha-color-on-disabled-quiet);
        }

        @media (hover: hover) {
          :host([appearance~="filled"])
            .button:not(.disabled):not(.loading):hover {
            background-color: var(--button-color-fill-normal-hover);
          }
          :host([appearance~="accent"])
            .button:not(.disabled):not(.loading):hover {
            background-color: var(--button-color-fill-loud-hover);
          }
          :host([appearance~="plain"])
            .button:not(.disabled):not(.loading):hover {
            color: var(--wa-color-on-normal);
          }
        }
        :host([appearance~="filled"]) .button {
          color: var(--wa-color-on-normal);
          background-color: var(--wa-color-fill-normal);
          border-color: transparent;
        }
        :host([appearance~="filled"])
          .button:not(.disabled):not(.loading):active {
          background-color: var(--button-color-fill-normal-active);
        }
        :host([appearance~="filled"]) .button.disabled {
          background-color: var(--ha-color-fill-disabled-normal-resting);
          color: var(--ha-color-on-disabled-normal);
        }

        :host([appearance~="accent"]) .button {
          background-color: var(
            --wa-color-fill-loud,
            var(--wa-color-neutral-fill-loud)
          );
        }
        :host([appearance~="accent"])
          .button:not(.disabled):not(.loading):active {
          background-color: var(--button-color-fill-loud-active);
        }
        :host([appearance~="accent"]) .button.disabled {
          background-color: var(--ha-color-fill-disabled-loud-resting);
          color: var(--ha-color-on-disabled-loud);
        }

        :host([loading]) {
          pointer-events: none;
        }

        .button.disabled {
          opacity: 1;
        }

        slot[name="start"]::slotted(*) {
          margin-inline-end: 4px;
        }
        slot[name="end"]::slotted(*) {
          margin-inline-start: 4px;
        }

        .button.has-start {
          padding-inline-start: 8px;
        }
        .button.has-end {
          padding-inline-end: 8px;
        }

        .label {
          overflow: hidden;
          text-overflow: ellipsis;
          padding: var(--ha-space-1) 0;
        }
      `]}constructor(...o){super(...o),this.variant="brand"}}s=(0,r.__decorate)([(0,n.EM)("ha-button")],s),t()}catch(s){t(s)}}))},49339:function(o,t,a){a.a(o,(async function(o,r){try{a.r(t);var e=a(62826),i=a(96196),n=a(77845),l=a(5871),s=(a(371),a(89473)),c=(a(45397),a(17963),o([s]));s=(c.then?(await c)():c)[0];class d extends i.WF{render(){return i.qy`
      ${this.toolbar?i.qy`<div class="toolbar">
            ${this.rootnav||history.state?.root?i.qy`
                  <ha-menu-button
                    .hass=${this.hass}
                    .narrow=${this.narrow}
                  ></ha-menu-button>
                `:i.qy`
                  <ha-icon-button-arrow-prev
                    .hass=${this.hass}
                    @click=${this._handleBack}
                  ></ha-icon-button-arrow-prev>
                `}
          </div>`:""}
      <div class="content">
        <ha-alert alert-type="error">${this.error}</ha-alert>
        <slot>
          <ha-button appearance="plain" size="small" @click=${this._handleBack}>
            ${this.hass?.localize("ui.common.back")}
          </ha-button>
        </slot>
      </div>
    `}_handleBack(){(0,l.O)()}static get styles(){return[i.AH`
        :host {
          display: block;
          height: 100%;
          background-color: var(--primary-background-color);
        }
        .toolbar {
          display: flex;
          align-items: center;
          font-size: var(--ha-font-size-xl);
          height: var(--header-height);
          padding: 8px 12px;
          pointer-events: none;
          background-color: var(--app-header-background-color);
          font-weight: var(--ha-font-weight-normal);
          color: var(--app-header-text-color, white);
          border-bottom: var(--app-header-border-bottom, none);
          box-sizing: border-box;
        }
        @media (max-width: 599px) {
          .toolbar {
            padding: 4px;
          }
        }
        ha-icon-button-arrow-prev {
          pointer-events: auto;
        }
        .content {
          color: var(--primary-text-color);
          height: calc(100% - var(--header-height));
          display: flex;
          padding: 16px;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          box-sizing: border-box;
        }
        a {
          color: var(--primary-color);
        }
        ha-alert {
          margin-bottom: 16px;
        }
      `]}constructor(...o){super(...o),this.toolbar=!0,this.rootnav=!1,this.narrow=!1}}(0,e.__decorate)([(0,n.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,e.__decorate)([(0,n.MZ)({type:Boolean})],d.prototype,"toolbar",void 0),(0,e.__decorate)([(0,n.MZ)({type:Boolean})],d.prototype,"rootnav",void 0),(0,e.__decorate)([(0,n.MZ)({type:Boolean})],d.prototype,"narrow",void 0),(0,e.__decorate)([(0,n.MZ)()],d.prototype,"error",void 0),d=(0,e.__decorate)([(0,n.EM)("hass-error-screen")],d),r()}catch(d){r(d)}}))},84884:function(o,t,a){var r=a(62826),e=a(96196),i=a(77845),n=a(94333),l=a(22786),s=a(55376),c=a(92209);const d=(o,t)=>!t.component||(0,s.e)(t.component).some((t=>(0,c.x)(o,t))),h=(o,t)=>!t.not_component||!(0,s.e)(t.not_component).some((t=>(0,c.x)(o,t))),p=o=>o.core,v=(o,t)=>(o=>o.advancedOnly)(t)&&!(o=>o.userData?.showAdvanced)(o);var b=a(5871),u=a(39501),f=(a(371),a(45397),a(60961),a(32288));a(95591);class m extends e.WF{render(){return e.qy`
      <div
        tabindex="0"
        role="tab"
        aria-selected=${this.active}
        aria-label=${(0,f.J)(this.name)}
        @keydown=${this._handleKeyDown}
      >
        ${this.narrow?e.qy`<slot name="icon"></slot>`:""}
        <span class="name">${this.name}</span>
        <ha-ripple></ha-ripple>
      </div>
    `}_handleKeyDown(o){"Enter"===o.key&&o.target.click()}constructor(...o){super(...o),this.active=!1,this.narrow=!1}}m.styles=e.AH`
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
  `,(0,r.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0})],m.prototype,"active",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0})],m.prototype,"narrow",void 0),(0,r.__decorate)([(0,i.MZ)()],m.prototype,"name",void 0),m=(0,r.__decorate)([(0,i.EM)("ha-tab")],m);var g=a(39396);class y extends e.WF{willUpdate(o){o.has("route")&&(this._activeTab=this.tabs.find((o=>`${this.route.prefix}${this.route.path}`.includes(o.path)))),super.willUpdate(o)}render(){const o=this._getTabs(this.tabs,this._activeTab,this.hass.config.components,this.hass.language,this.hass.userData,this.narrow,this.localizeFunc||this.hass.localize),t=o.length>1;return e.qy`
      <div class="toolbar">
        <slot name="toolbar">
          <div class="toolbar-content">
            ${this.mainPage||!this.backPath&&history.state?.root?e.qy`
                  <ha-menu-button
                    .hassio=${this.supervisor}
                    .hass=${this.hass}
                    .narrow=${this.narrow}
                  ></ha-menu-button>
                `:this.backPath?e.qy`
                    <a href=${this.backPath}>
                      <ha-icon-button-arrow-prev
                        .hass=${this.hass}
                      ></ha-icon-button-arrow-prev>
                    </a>
                  `:e.qy`
                    <ha-icon-button-arrow-prev
                      .hass=${this.hass}
                      @click=${this._backTapped}
                    ></ha-icon-button-arrow-prev>
                  `}
            ${this.narrow||!t?e.qy`<div class="main-title">
                  <slot name="header">${t?"":o[0]}</slot>
                </div>`:""}
            ${t&&!this.narrow?e.qy`<div id="tabbar">${o}</div>`:""}
            <div id="toolbar-icon">
              <slot name="toolbar-icon"></slot>
            </div>
          </div>
        </slot>
        ${t&&this.narrow?e.qy`<div id="tabbar" class="bottom-bar">${o}</div>`:""}
      </div>
      <div
        class=${(0,n.H)({container:!0,tabs:t&&this.narrow})}
      >
        ${this.pane?e.qy`<div class="pane">
              <div class="shadow-container"></div>
              <div class="ha-scrollbar">
                <slot name="pane"></slot>
              </div>
            </div>`:e.s6}
        <div
          class="content ha-scrollbar ${(0,n.H)({tabs:t})}"
          @scroll=${this._saveScrollPos}
        >
          <slot></slot>
          ${this.hasFab?e.qy`<div class="fab-bottom-space"></div>`:e.s6}
        </div>
      </div>
      <div id="fab" class=${(0,n.H)({tabs:t})}>
        <slot name="fab"></slot>
      </div>
    `}_saveScrollPos(o){this._savedScrollPos=o.target.scrollTop}_backTapped(){this.backCallback?this.backCallback():(0,b.O)()}static get styles(){return[g.dp,e.AH`
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
      `]}constructor(...o){super(...o),this.supervisor=!1,this.mainPage=!1,this.narrow=!1,this.isWide=!1,this.pane=!1,this.hasFab=!1,this._getTabs=(0,l.A)(((o,t,a,r,i,n,l)=>{const s=o.filter((o=>((o,t)=>(p(t)||d(o,t))&&!v(o,t)&&h(o,t))(this.hass,o)));if(s.length<2){if(1===s.length){const o=s[0];return[o.translationKey?l(o.translationKey):o.name]}return[""]}return s.map((o=>e.qy`
          <a href=${o.path}>
            <ha-tab
              .hass=${this.hass}
              .active=${o.path===t?.path}
              .narrow=${this.narrow}
              .name=${o.translationKey?l(o.translationKey):o.name}
            >
              ${o.iconPath?e.qy`<ha-svg-icon
                    slot="icon"
                    .path=${o.iconPath}
                  ></ha-svg-icon>`:""}
            </ha-tab>
          </a>
        `))}))}}(0,r.__decorate)([(0,i.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean})],y.prototype,"supervisor",void 0),(0,r.__decorate)([(0,i.MZ)({attribute:!1})],y.prototype,"localizeFunc",void 0),(0,r.__decorate)([(0,i.MZ)({type:String,attribute:"back-path"})],y.prototype,"backPath",void 0),(0,r.__decorate)([(0,i.MZ)({attribute:!1})],y.prototype,"backCallback",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean,attribute:"main-page"})],y.prototype,"mainPage",void 0),(0,r.__decorate)([(0,i.MZ)({attribute:!1})],y.prototype,"route",void 0),(0,r.__decorate)([(0,i.MZ)({attribute:!1})],y.prototype,"tabs",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0})],y.prototype,"narrow",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0,attribute:"is-wide"})],y.prototype,"isWide",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean})],y.prototype,"pane",void 0),(0,r.__decorate)([(0,i.MZ)({type:Boolean,attribute:"has-fab"})],y.prototype,"hasFab",void 0),(0,r.__decorate)([(0,i.wk)()],y.prototype,"_activeTab",void 0),(0,r.__decorate)([(0,u.a)(".content")],y.prototype,"_savedScrollPos",void 0),(0,r.__decorate)([(0,i.Ls)({passive:!0})],y.prototype,"_saveScrollPos",null),y=(0,r.__decorate)([(0,i.EM)("hass-tabs-subpage")],y)},64576:function(o,t,a){a.a(o,(async function(o,r){try{a.r(t),a.d(t,{KNXError:()=>d});var e=a(62826),i=a(96196),n=a(77845),l=a(76679),s=(a(84884),a(49339)),c=o([s]);s=(c.then?(await c)():c)[0];class d extends i.WF{render(){const o=l.G.history.state?.message??"Unknown error";return i.qy`
      <hass-error-screen
        .hass=${this.hass}
        .error=${o}
        .toolbar=${!0}
        .rootnav=${!1}
        .narrow=${this.narrow}
      ></hass-error-screen>
    `}}(0,e.__decorate)([(0,n.MZ)({type:Object})],d.prototype,"hass",void 0),(0,e.__decorate)([(0,n.MZ)({attribute:!1})],d.prototype,"knx",void 0),(0,e.__decorate)([(0,n.MZ)({type:Boolean,reflect:!0})],d.prototype,"narrow",void 0),(0,e.__decorate)([(0,n.MZ)({type:Object})],d.prototype,"route",void 0),(0,e.__decorate)([(0,n.MZ)({type:Array,reflect:!1})],d.prototype,"tabs",void 0),d=(0,e.__decorate)([(0,n.EM)("knx-error")],d),r()}catch(d){r(d)}}))}};
//# sourceMappingURL=7257.5ac32e5c70c42b32.js.map