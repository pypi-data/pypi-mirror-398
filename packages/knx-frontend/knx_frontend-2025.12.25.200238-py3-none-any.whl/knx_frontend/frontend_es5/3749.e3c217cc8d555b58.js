"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3749"],{55376:function(t,e,a){function o(t){return null==t||Array.isArray(t)?t:[t]}a.d(e,{e:function(){return o}})},92209:function(t,e,a){a.d(e,{x:function(){return o}});a(74423);var o=(t,e)=>t&&t.config.components.includes(e)},39501:function(t,e,a){a.d(e,{a:function(){return r}});a(16280);var o=(0,a(62111).n)((t=>{history.replaceState({scrollPosition:t},"")}),300);function r(t){return(e,a)=>{if("object"==typeof a)throw new Error("This decorator does not support this compilation type.");var r=e.connectedCallback;e.connectedCallback=function(){r.call(this);var e=this[a];e&&this.updateComplete.then((()=>{var a=this.renderRoot.querySelector(t);a&&setTimeout((()=>{a.scrollTop=e}),0)}))};var i,n=Object.getOwnPropertyDescriptor(e,a);if(void 0===n)i={get(){var t;return this[`__${String(a)}`]||(null===(t=history.state)||void 0===t?void 0:t.scrollPosition)},set(t){o(t),this[`__${String(a)}`]=t},configurable:!0,enumerable:!0};else{var s=n.set;i=Object.assign(Object.assign({},n),{},{set(t){o(t),this[`__${String(a)}`]=t,null==s||s.call(this,t)}})}Object.defineProperty(e,a,i)}}},62111:function(t,e,a){a.d(e,{n:function(){return o}});var o=function(t,e){var a,o=!(arguments.length>2&&void 0!==arguments[2])||arguments[2],r=!(arguments.length>3&&void 0!==arguments[3])||arguments[3],i=0,n=function(){for(var n=arguments.length,s=new Array(n),l=0;l<n;l++)s[l]=arguments[l];var c=Date.now();i||!1!==o||(i=c);var d=e-(c-i);d<=0||d>e?(a&&(clearTimeout(a),a=void 0),i=c,t.apply(void 0,s)):a||!1===r||(a=window.setTimeout((()=>{i=!1===o?0:Date.now(),a=void 0,t.apply(void 0,s)}),d))};return n.cancel=()=>{clearTimeout(a),a=void 0,i=0},n}},95591:function(t,e,a){var o,r=a(44734),i=a(56038),n=a(75864),s=a(69683),l=a(6454),c=a(25460),d=(a(28706),a(62826)),h=a(76482),p=a(91382),v=a(96245),b=a(96196),u=a(77845),f=function(t){function e(){var t;(0,r.A)(this,e);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(t=(0,s.A)(this,e,[].concat(o))).attachableTouchController=new h.i((0,n.A)(t),t._onTouchControlChange.bind((0,n.A)(t))),t._handleTouchEnd=()=>{t.disabled||(0,c.A)(((0,n.A)(t),e),"endPressAnimation",t,3)([])},t}return(0,l.A)(e,t),(0,i.A)(e,[{key:"attach",value:function(t){(0,c.A)(e,"attach",this,3)([t]),this.attachableTouchController.attach(t)}},{key:"disconnectedCallback",value:function(){(0,c.A)(e,"disconnectedCallback",this,3)([]),this.hovered=!1,this.pressed=!1}},{key:"detach",value:function(){(0,c.A)(e,"detach",this,3)([]),this.attachableTouchController.detach()}},{key:"_onTouchControlChange",value:function(t,e){null==t||t.removeEventListener("touchend",this._handleTouchEnd),null==e||e.addEventListener("touchend",this._handleTouchEnd)}}])}(p.n);f.styles=[v.R,(0,b.AH)(o||(o=(t=>t)`
      :host {
        --md-ripple-hover-opacity: var(--ha-ripple-hover-opacity, 0.08);
        --md-ripple-pressed-opacity: var(--ha-ripple-pressed-opacity, 0.12);
        --md-ripple-hover-color: var(
          --ha-ripple-hover-color,
          var(--ha-ripple-color, var(--secondary-text-color))
        );
        --md-ripple-pressed-color: var(
          --ha-ripple-pressed-color,
          var(--ha-ripple-color, var(--secondary-text-color))
        );
      }
    `))],f=(0,d.__decorate)([(0,u.EM)("ha-ripple")],f)},84884:function(t,e,a){var o,r,i,n=a(44734),s=a(56038),l=a(69683),c=a(6454),d=a(25460),h=(a(28706),a(2008),a(50113),a(74423),a(62062),a(18111),a(22489),a(20116),a(61701),a(26099),a(62826)),p=a(96196),v=a(77845),b=a(94333),u=a(22786),f=(a(13579),a(55376)),y=a(92209),g=(t,e)=>!e.component||(0,f.e)(e.component).some((e=>(0,y.x)(t,e))),m=(t,e)=>!e.not_component||!(0,f.e)(e.not_component).some((e=>(0,y.x)(t,e))),x=t=>t.core,w=(t,e)=>(t=>t.advancedOnly)(e)&&!(t=>{var e;return null===(e=t.userData)||void 0===e?void 0:e.showAdvanced})(t),_=a(5871),k=a(39501),$=(a(371),a(45397),a(60961),a(32288)),A=(a(95591),t=>t),T=function(t){function e(){var t;(0,n.A)(this,e);for(var a=arguments.length,o=new Array(a),r=0;r<a;r++)o[r]=arguments[r];return(t=(0,l.A)(this,e,[].concat(o))).active=!1,t.narrow=!1,t}return(0,c.A)(e,t),(0,s.A)(e,[{key:"render",value:function(){return(0,p.qy)(o||(o=A`
      <div
        tabindex="0"
        role="tab"
        aria-selected=${0}
        aria-label=${0}
        @keydown=${0}
      >
        ${0}
        <span class="name">${0}</span>
        <ha-ripple></ha-ripple>
      </div>
    `),this.active,(0,$.J)(this.name),this._handleKeyDown,this.narrow?(0,p.qy)(r||(r=A`<slot name="icon"></slot>`)):"",this.name)}},{key:"_handleKeyDown",value:function(t){"Enter"===t.key&&t.target.click()}}])}(p.WF);T.styles=(0,p.AH)(i||(i=A`
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
  `)),(0,h.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0})],T.prototype,"active",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0})],T.prototype,"narrow",void 0),(0,h.__decorate)([(0,v.MZ)()],T.prototype,"name",void 0),T=(0,h.__decorate)([(0,v.EM)("ha-tab")],T);var P,M,C,z,Z,q,S,j,E,B,D,F,O=a(39396),H=t=>t,K=function(t){function e(){var t;(0,n.A)(this,e);for(var a=arguments.length,o=new Array(a),r=0;r<a;r++)o[r]=arguments[r];return(t=(0,l.A)(this,e,[].concat(o))).supervisor=!1,t.mainPage=!1,t.narrow=!1,t.isWide=!1,t.pane=!1,t.hasFab=!1,t._getTabs=(0,u.A)(((e,a,o,r,i,n,s)=>{var l=e.filter((e=>((t,e)=>(x(e)||g(t,e))&&!w(t,e)&&m(t,e))(t.hass,e)));if(l.length<2){if(1===l.length){var c=l[0];return[c.translationKey?s(c.translationKey):c.name]}return[""]}return l.map((e=>(0,p.qy)(P||(P=H`
          <a href=${0}>
            <ha-tab
              .hass=${0}
              .active=${0}
              .narrow=${0}
              .name=${0}
            >
              ${0}
            </ha-tab>
          </a>
        `),e.path,t.hass,e.path===(null==a?void 0:a.path),t.narrow,e.translationKey?s(e.translationKey):e.name,e.iconPath?(0,p.qy)(M||(M=H`<ha-svg-icon
                    slot="icon"
                    .path=${0}
                  ></ha-svg-icon>`),e.iconPath):"")))})),t}return(0,c.A)(e,t),(0,s.A)(e,[{key:"willUpdate",value:function(t){t.has("route")&&(this._activeTab=this.tabs.find((t=>`${this.route.prefix}${this.route.path}`.includes(t.path)))),(0,d.A)(e,"willUpdate",this,3)([t])}},{key:"render",value:function(){var t,e=this._getTabs(this.tabs,this._activeTab,this.hass.config.components,this.hass.language,this.hass.userData,this.narrow,this.localizeFunc||this.hass.localize),a=e.length>1;return(0,p.qy)(C||(C=H`
      <div class="toolbar">
        <slot name="toolbar">
          <div class="toolbar-content">
            ${0}
            ${0}
            ${0}
            <div id="toolbar-icon">
              <slot name="toolbar-icon"></slot>
            </div>
          </div>
        </slot>
        ${0}
      </div>
      <div
        class=${0}
      >
        ${0}
        <div
          class="content ha-scrollbar ${0}"
          @scroll=${0}
        >
          <slot></slot>
          ${0}
        </div>
      </div>
      <div id="fab" class=${0}>
        <slot name="fab"></slot>
      </div>
    `),this.mainPage||!this.backPath&&null!==(t=history.state)&&void 0!==t&&t.root?(0,p.qy)(z||(z=H`
                  <ha-menu-button
                    .hassio=${0}
                    .hass=${0}
                    .narrow=${0}
                  ></ha-menu-button>
                `),this.supervisor,this.hass,this.narrow):this.backPath?(0,p.qy)(Z||(Z=H`
                    <a href=${0}>
                      <ha-icon-button-arrow-prev
                        .hass=${0}
                      ></ha-icon-button-arrow-prev>
                    </a>
                  `),this.backPath,this.hass):(0,p.qy)(q||(q=H`
                    <ha-icon-button-arrow-prev
                      .hass=${0}
                      @click=${0}
                    ></ha-icon-button-arrow-prev>
                  `),this.hass,this._backTapped),this.narrow||!a?(0,p.qy)(S||(S=H`<div class="main-title">
                  <slot name="header">${0}</slot>
                </div>`),a?"":e[0]):"",a&&!this.narrow?(0,p.qy)(j||(j=H`<div id="tabbar">${0}</div>`),e):"",a&&this.narrow?(0,p.qy)(E||(E=H`<div id="tabbar" class="bottom-bar">${0}</div>`),e):"",(0,b.H)({container:!0,tabs:a&&this.narrow}),this.pane?(0,p.qy)(B||(B=H`<div class="pane">
              <div class="shadow-container"></div>
              <div class="ha-scrollbar">
                <slot name="pane"></slot>
              </div>
            </div>`)):p.s6,(0,b.H)({tabs:a}),this._saveScrollPos,this.hasFab?(0,p.qy)(D||(D=H`<div class="fab-bottom-space"></div>`)):p.s6,(0,b.H)({tabs:a}))}},{key:"_saveScrollPos",value:function(t){this._savedScrollPos=t.target.scrollTop}},{key:"_backTapped",value:function(){this.backCallback?this.backCallback():(0,_.O)()}}],[{key:"styles",get:function(){return[O.dp,(0,p.AH)(F||(F=H`
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
      `))]}}])}(p.WF);(0,h.__decorate)([(0,v.MZ)({attribute:!1})],K.prototype,"hass",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],K.prototype,"supervisor",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],K.prototype,"localizeFunc",void 0),(0,h.__decorate)([(0,v.MZ)({type:String,attribute:"back-path"})],K.prototype,"backPath",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],K.prototype,"backCallback",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,attribute:"main-page"})],K.prototype,"mainPage",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],K.prototype,"route",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],K.prototype,"tabs",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0})],K.prototype,"narrow",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0,attribute:"is-wide"})],K.prototype,"isWide",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],K.prototype,"pane",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,attribute:"has-fab"})],K.prototype,"hasFab",void 0),(0,h.__decorate)([(0,v.wk)()],K.prototype,"_activeTab",void 0),(0,h.__decorate)([(0,k.a)(".content")],K.prototype,"_savedScrollPos",void 0),(0,h.__decorate)([(0,v.Ls)({passive:!0})],K.prototype,"_saveScrollPos",null),K=(0,h.__decorate)([(0,v.EM)("hass-tabs-subpage")],K)}}]);
//# sourceMappingURL=3749.e3c217cc8d555b58.js.map