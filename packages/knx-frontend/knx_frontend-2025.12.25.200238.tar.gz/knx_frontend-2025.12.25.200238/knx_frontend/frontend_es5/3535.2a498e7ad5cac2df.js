"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3535"],{371:function(t,a,o){o.r(a),o.d(a,{HaIconButtonArrowPrev:function(){return p}});var i,e=o(44734),n=o(56038),r=o(69683),s=o(6454),h=(o(28706),o(62826)),c=o(96196),l=o(77845),d=o(76679),u=(o(60733),t=>t),p=function(t){function a(){var t;(0,e.A)(this,a);for(var o=arguments.length,i=new Array(o),n=0;n<o;n++)i[n]=arguments[n];return(t=(0,r.A)(this,a,[].concat(i))).disabled=!1,t._icon="rtl"===d.G.document.dir?"M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z":"M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z",t}return(0,s.A)(a,t),(0,n.A)(a,[{key:"render",value:function(){var t;return(0,c.qy)(i||(i=u`
      <ha-icon-button
        .disabled=${0}
        .label=${0}
        .path=${0}
      ></ha-icon-button>
    `),this.disabled,this.label||(null===(t=this.hass)||void 0===t?void 0:t.localize("ui.common.back"))||"Back",this._icon)}}])}(c.WF);(0,h.__decorate)([(0,l.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,h.__decorate)([(0,l.MZ)({type:Boolean})],p.prototype,"disabled",void 0),(0,h.__decorate)([(0,l.MZ)()],p.prototype,"label",void 0),(0,h.__decorate)([(0,l.wk)()],p.prototype,"_icon",void 0),p=(0,h.__decorate)([(0,l.EM)("ha-icon-button-arrow-prev")],p)},60733:function(t,a,o){o.r(a),o.d(a,{HaIconButton:function(){return g}});var i,e,n,r,s=o(44734),h=o(56038),c=o(69683),l=o(6454),d=(o(28706),o(62826)),u=(o(11677),o(96196)),p=o(77845),f=o(32288),v=(o(60961),t=>t),g=function(t){function a(){var t;(0,s.A)(this,a);for(var o=arguments.length,i=new Array(o),e=0;e<o;e++)i[e]=arguments[e];return(t=(0,c.A)(this,a,[].concat(i))).disabled=!1,t.hideTitle=!1,t}return(0,l.A)(a,t),(0,h.A)(a,[{key:"focus",value:function(){var t;null===(t=this._button)||void 0===t||t.focus()}},{key:"render",value:function(){return(0,u.qy)(i||(i=v`
      <mwc-icon-button
        aria-label=${0}
        title=${0}
        aria-haspopup=${0}
        .disabled=${0}
      >
        ${0}
      </mwc-icon-button>
    `),(0,f.J)(this.label),(0,f.J)(this.hideTitle?void 0:this.label),(0,f.J)(this.ariaHasPopup),this.disabled,this.path?(0,u.qy)(e||(e=v`<ha-svg-icon .path=${0}></ha-svg-icon>`),this.path):(0,u.qy)(n||(n=v`<slot></slot>`)))}}])}(u.WF);g.shadowRootOptions={mode:"open",delegatesFocus:!0},g.styles=(0,u.AH)(r||(r=v`
    :host {
      display: inline-block;
      outline: none;
    }
    :host([disabled]) {
      pointer-events: none;
    }
    mwc-icon-button {
      --mdc-theme-on-primary: currentColor;
      --mdc-theme-text-disabled-on-light: var(--disabled-text-color);
    }
  `)),(0,d.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],g.prototype,"disabled",void 0),(0,d.__decorate)([(0,p.MZ)({type:String})],g.prototype,"path",void 0),(0,d.__decorate)([(0,p.MZ)({type:String})],g.prototype,"label",void 0),(0,d.__decorate)([(0,p.MZ)({type:String,attribute:"aria-haspopup"})],g.prototype,"ariaHasPopup",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:"hide-title",type:Boolean})],g.prototype,"hideTitle",void 0),(0,d.__decorate)([(0,p.P)("mwc-icon-button",!0)],g.prototype,"_button",void 0),g=(0,d.__decorate)([(0,p.EM)("ha-icon-button")],g)},45397:function(t,a,o){var i,e,n,r=o(44734),s=o(56038),h=o(69683),c=o(6454),l=o(25460),d=(o(16280),o(28706),o(2892),o(62826)),u=o(96196),p=o(77845),f=o(92542),v=(o(16034),function(){return(0,s.A)((function t(){(0,r.A)(this,t),this.notifications={}}),[{key:"processMessage",value:function(t){if("removed"===t.type)for(var a=0,o=Object.keys(t.notifications);a<o.length;a++){var i=o[a];delete this.notifications[i]}else this.notifications=Object.assign(Object.assign({},this.notifications),t.notifications);return Object.values(this.notifications)}}])}()),g=(o(60733),t=>t),m=function(t){function a(){var t;(0,r.A)(this,a);for(var o=arguments.length,i=new Array(o),e=0;e<o;e++)i[e]=arguments[e];return(t=(0,h.A)(this,a,[].concat(i))).hassio=!1,t.narrow=!1,t._hasNotifications=!1,t._show=!1,t._alwaysVisible=!1,t._attachNotifOnConnect=!1,t}return(0,c.A)(a,t),(0,s.A)(a,[{key:"connectedCallback",value:function(){(0,l.A)(a,"connectedCallback",this,3)([]),this._attachNotifOnConnect&&(this._attachNotifOnConnect=!1,this._subscribeNotifications())}},{key:"disconnectedCallback",value:function(){(0,l.A)(a,"disconnectedCallback",this,3)([]),this._unsubNotifications&&(this._attachNotifOnConnect=!0,this._unsubNotifications(),this._unsubNotifications=void 0)}},{key:"render",value:function(){if(!this._show)return u.s6;var t=this._hasNotifications&&(this.narrow||"always_hidden"===this.hass.dockedSidebar);return(0,u.qy)(i||(i=g`
      <ha-icon-button
        .label=${0}
        .path=${0}
        @click=${0}
      ></ha-icon-button>
      ${0}
    `),this.hass.localize("ui.sidebar.sidebar_toggle"),"M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z",this._toggleMenu,t?(0,u.qy)(e||(e=g`<div class="dot"></div>`)):"")}},{key:"firstUpdated",value:function(t){(0,l.A)(a,"firstUpdated",this,3)([t]),this.hassio&&(this._alwaysVisible=(Number(window.parent.frontendVersion)||0)<20190710)}},{key:"willUpdate",value:function(t){if((0,l.A)(a,"willUpdate",this,3)([t]),t.has("narrow")||t.has("hass")){var o=t.has("hass")?t.get("hass"):this.hass,i=(t.has("narrow")?t.get("narrow"):this.narrow)||"always_hidden"===(null==o?void 0:o.dockedSidebar),e=this.narrow||"always_hidden"===this.hass.dockedSidebar;this.hasUpdated&&i===e||(this._show=e||this._alwaysVisible,e?this._subscribeNotifications():this._unsubNotifications&&(this._unsubNotifications(),this._unsubNotifications=void 0))}}},{key:"_subscribeNotifications",value:function(){if(this._unsubNotifications)throw new Error("Already subscribed");var t,a,o,i;this._unsubNotifications=(t=this.hass.connection,a=t=>{this._hasNotifications=t.length>0},o=new v,i=t.subscribeMessage((t=>a(o.processMessage(t))),{type:"persistent_notification/subscribe"}),()=>{i.then((t=>null==t?void 0:t()))})}},{key:"_toggleMenu",value:function(){(0,f.r)(this,"hass-toggle-menu")}}])}(u.WF);m.styles=(0,u.AH)(n||(n=g`
    :host {
      position: relative;
    }
    .dot {
      pointer-events: none;
      position: absolute;
      background-color: var(--accent-color);
      width: 12px;
      height: 12px;
      top: 9px;
      right: 7px;
      inset-inline-end: 7px;
      inset-inline-start: initial;
      border-radius: var(--ha-border-radius-circle);
      border: 2px solid var(--app-header-background-color);
    }
  `)),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],m.prototype,"hassio",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],m.prototype,"narrow",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,d.__decorate)([(0,p.wk)()],m.prototype,"_hasNotifications",void 0),(0,d.__decorate)([(0,p.wk)()],m.prototype,"_show",void 0),m=(0,d.__decorate)([(0,p.EM)("ha-menu-button")],m)},60961:function(t,a,o){o.r(a),o.d(a,{HaSvgIcon:function(){return v}});var i,e,n,r,s=o(44734),h=o(56038),c=o(69683),l=o(6454),d=o(62826),u=o(96196),p=o(77845),f=t=>t,v=function(t){function a(){return(0,s.A)(this,a),(0,c.A)(this,a,arguments)}return(0,l.A)(a,t),(0,h.A)(a,[{key:"render",value:function(){return(0,u.JW)(i||(i=f`
    <svg
      viewBox=${0}
      preserveAspectRatio="xMidYMid meet"
      focusable="false"
      role="img"
      aria-hidden="true"
    >
      <g>
        ${0}
        ${0}
      </g>
    </svg>`),this.viewBox||"0 0 24 24",this.path?(0,u.JW)(e||(e=f`<path class="primary-path" d=${0}></path>`),this.path):u.s6,this.secondaryPath?(0,u.JW)(n||(n=f`<path class="secondary-path" d=${0}></path>`),this.secondaryPath):u.s6)}}])}(u.WF);v.styles=(0,u.AH)(r||(r=f`
    :host {
      display: var(--ha-icon-display, inline-flex);
      align-items: center;
      justify-content: center;
      position: relative;
      vertical-align: middle;
      fill: var(--icon-primary-color, currentcolor);
      width: var(--mdc-icon-size, 24px);
      height: var(--mdc-icon-size, 24px);
    }
    svg {
      width: 100%;
      height: 100%;
      pointer-events: none;
      display: block;
    }
    path.primary-path {
      opacity: var(--icon-primary-opactity, 1);
    }
    path.secondary-path {
      fill: var(--icon-secondary-color, currentcolor);
      opacity: var(--icon-secondary-opactity, 0.5);
    }
  `)),(0,d.__decorate)([(0,p.MZ)()],v.prototype,"path",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"secondaryPath",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"viewBox",void 0),v=(0,d.__decorate)([(0,p.EM)("ha-svg-icon")],v)},39396:function(t,a,o){o.d(a,{RF:function(){return u},dp:function(){return v},kO:function(){return f},nA:function(){return p},og:function(){return d}});var i,e,n,r,s,h,c=o(96196),l=t=>t,d=(0,c.AH)(i||(i=l`
  button.link {
    background: none;
    color: inherit;
    border: none;
    padding: 0;
    font: inherit;
    text-align: left;
    text-decoration: underline;
    cursor: pointer;
    outline: none;
  }
`)),u=(0,c.AH)(e||(e=l`
  :host {
    font-family: var(--ha-font-family-body);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    font-size: var(--ha-font-size-m);
    font-weight: var(--ha-font-weight-normal);
    line-height: var(--ha-line-height-normal);
  }

  app-header div[sticky] {
    height: 48px;
  }

  app-toolbar [main-title] {
    margin-left: 20px;
    margin-inline-start: 20px;
    margin-inline-end: initial;
  }

  h1 {
    font-family: var(--ha-font-family-heading);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    font-size: var(--ha-font-size-2xl);
    font-weight: var(--ha-font-weight-normal);
    line-height: var(--ha-line-height-condensed);
  }

  h2 {
    font-family: var(--ha-font-family-body);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: var(--ha-font-size-xl);
    font-weight: var(--ha-font-weight-medium);
    line-height: var(--ha-line-height-normal);
  }

  h3 {
    font-family: var(--ha-font-family-body);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    font-size: var(--ha-font-size-l);
    font-weight: var(--ha-font-weight-normal);
    line-height: var(--ha-line-height-normal);
  }

  a {
    color: var(--primary-color);
  }

  .secondary {
    color: var(--secondary-text-color);
  }

  .error {
    color: var(--error-color);
  }

  .warning {
    color: var(--error-color);
  }

  ${0}

  .card-actions a {
    text-decoration: none;
  }

  .card-actions .warning {
    --mdc-theme-primary: var(--error-color);
  }

  .layout.horizontal,
  .layout.vertical {
    display: flex;
  }
  .layout.inline {
    display: inline-flex;
  }
  .layout.horizontal {
    flex-direction: row;
  }
  .layout.vertical {
    flex-direction: column;
  }
  .layout.wrap {
    flex-wrap: wrap;
  }
  .layout.no-wrap {
    flex-wrap: nowrap;
  }
  .layout.center,
  .layout.center-center {
    align-items: center;
  }
  .layout.bottom {
    align-items: flex-end;
  }
  .layout.center-justified,
  .layout.center-center {
    justify-content: center;
  }
  .flex {
    flex: 1;
    flex-basis: 0.000000001px;
  }
  .flex-auto {
    flex: 1 1 auto;
  }
  .flex-none {
    flex: none;
  }
  .layout.justified {
    justify-content: space-between;
  }
`),d),p=(0,c.AH)(n||(n=l`
  /* mwc-dialog (ha-dialog) styles */
  ha-dialog {
    --mdc-dialog-min-width: 400px;
    --mdc-dialog-max-width: 600px;
    --mdc-dialog-max-width: min(600px, 95vw);
    --justify-action-buttons: space-between;
    --dialog-container-padding: var(--safe-area-inset-top, var(--ha-space-0))
      var(--safe-area-inset-right, var(--ha-space-0))
      var(--safe-area-inset-bottom, var(--ha-space-0))
      var(--safe-area-inset-left, var(--ha-space-0));
    --dialog-surface-padding: var(--ha-space-0);
  }

  ha-dialog .form {
    color: var(--primary-text-color);
  }

  a {
    color: var(--primary-color);
  }

  /* make dialog fullscreen on small screens */
  @media all and (max-width: 450px), all and (max-height: 500px) {
    ha-dialog {
      --mdc-dialog-min-width: 100vw;
      --mdc-dialog-max-width: 100vw;
      --mdc-dialog-min-height: 100vh;
      --mdc-dialog-min-height: 100svh;
      --mdc-dialog-max-height: 100vh;
      --mdc-dialog-max-height: 100svh;
      --dialog-container-padding: var(--ha-space-0);
      --dialog-surface-padding: var(--safe-area-inset-top, var(--ha-space-0))
        var(--safe-area-inset-right, var(--ha-space-0))
        var(--safe-area-inset-bottom, var(--ha-space-0))
        var(--safe-area-inset-left, var(--ha-space-0));
      --vertical-align-dialog: flex-end;
      --ha-dialog-border-radius: var(--ha-border-radius-square);
    }
  }
  .error {
    color: var(--error-color);
  }
`)),f=(0,c.AH)(r||(r=l`
  ha-dialog {
    /* Pin dialog to top so it doesn't jump when content changes size */
    --vertical-align-dialog: flex-start;
    --dialog-surface-margin-top: var(--ha-space-10);
    --mdc-dialog-max-height: calc(
      100vh - var(--dialog-surface-margin-top) - var(--ha-space-2) - var(
          --safe-area-inset-y,
          var(--ha-space-0)
        )
    );
    --mdc-dialog-max-height: calc(
      100svh - var(--dialog-surface-margin-top) - var(--ha-space-2) - var(
          --safe-area-inset-y,
          var(--ha-space-0)
        )
    );
  }

  @media all and (max-width: 450px), all and (max-height: 500px) {
    ha-dialog {
      /* When in fullscreen, dialog should be attached to top */
      --dialog-surface-margin-top: var(--ha-space-0);
      --mdc-dialog-min-height: 100vh;
      --mdc-dialog-min-height: 100svh;
      --mdc-dialog-max-height: 100vh;
      --mdc-dialog-max-height: 100svh;
    }
  }
`)),v=(0,c.AH)(s||(s=l`
  .ha-scrollbar::-webkit-scrollbar {
    width: 0.4rem;
    height: 0.4rem;
  }

  .ha-scrollbar::-webkit-scrollbar-thumb {
    border-radius: var(--ha-border-radius-sm);
    background: var(--scrollbar-thumb-color);
  }

  .ha-scrollbar {
    overflow-y: auto;
    scrollbar-color: var(--scrollbar-thumb-color) transparent;
    scrollbar-width: thin;
  }
`));(0,c.AH)(h||(h=l`
  body {
    background-color: var(--primary-background-color);
    color: var(--primary-text-color);
    height: calc(100vh - 32px);
    width: 100vw;
  }
`))}}]);
//# sourceMappingURL=3535.2a498e7ad5cac2df.js.map