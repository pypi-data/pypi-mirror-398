"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7683"],{42256:function(e,t,i){i.d(t,{I:function(){return s}});var a=i(44734),r=i(56038),o=(i(16280),i(25276),i(44114),i(54554),i(18111),i(7588),i(33110),i(26099),i(58335),i(23500),function(){return(0,r.A)((function e(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:window.localStorage;(0,a.A)(this,e),this._storage={},this._listeners={},this.storage=t,this.storage===window.localStorage&&window.addEventListener("storage",(e=>{e.key&&this.hasKey(e.key)&&(this._storage[e.key]=e.newValue?JSON.parse(e.newValue):e.newValue,this._listeners[e.key]&&this._listeners[e.key].forEach((t=>t(e.oldValue?JSON.parse(e.oldValue):e.oldValue,this._storage[e.key]))))}))}),[{key:"addFromStorage",value:function(e){if(!this._storage[e]){var t=this.storage.getItem(e);t&&(this._storage[e]=JSON.parse(t))}}},{key:"subscribeChanges",value:function(e,t){return this._listeners[e]?this._listeners[e].push(t):this._listeners[e]=[t],()=>{this.unsubscribeChanges(e,t)}}},{key:"unsubscribeChanges",value:function(e,t){if(e in this._listeners){var i=this._listeners[e].indexOf(t);-1!==i&&this._listeners[e].splice(i,1)}}},{key:"hasKey",value:function(e){return e in this._storage}},{key:"getValue",value:function(e){return this._storage[e]}},{key:"setValue",value:function(e,t){var i=this._storage[e];this._storage[e]=t;try{void 0===t?this.storage.removeItem(e):this.storage.setItem(e,JSON.stringify(t))}catch(a){}finally{this._listeners[e]&&this._listeners[e].forEach((e=>e(i,t)))}}}])}()),n={};function s(e){return(t,i)=>{if("object"==typeof i)throw new Error("This decorator does not support this compilation type.");var a,r=e.storage||"localStorage";r&&r in n?a=n[r]:(a=new o(window[r]),n[r]=a);var s=e.key||String(i);a.addFromStorage(s);var c=!1!==e.subscribe?e=>a.subscribeChanges(s,((t,a)=>{e.requestUpdate(i,t)})):void 0,d=()=>a.hasKey(s)?e.deserializer?e.deserializer(a.getValue(s)):a.getValue(s):void 0,l=(t,r)=>{var o;e.state&&(o=d()),a.setValue(s,e.serializer?e.serializer(r):r),e.state&&t.requestUpdate(i,o)},h=t.performUpdate;if(t.performUpdate=function(){this.__initialized=!0,h.call(this)},e.subscribe){var u=t.connectedCallback,p=t.disconnectedCallback;t.connectedCallback=function(){u.call(this);this.__unbsubLocalStorage||(this.__unbsubLocalStorage=null==c?void 0:c(this))},t.disconnectedCallback=function(){var e;p.call(this);var t=this;null===(e=t.__unbsubLocalStorage)||void 0===e||e.call(t),t.__unbsubLocalStorage=void 0}}var m,_=Object.getOwnPropertyDescriptor(t,i);if(void 0===_)m={get(){return d()},set(e){(this.__initialized||void 0===d())&&l(this,e)},configurable:!0,enumerable:!0};else{var v=_.set;m=Object.assign(Object.assign({},_),{},{get(){return d()},set(e){(this.__initialized||void 0===d())&&l(this,e),null==v||v.call(this,e)}})}Object.defineProperty(t,i,m)}}},4657:function(e,t,i){i.d(t,{l:function(){return o}});var a=i(61397),r=i(50264),o=function(){var e=(0,r.A)((0,a.A)().m((function e(t,i){var r,o;return(0,a.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(!navigator.clipboard){e.n=4;break}return e.p=1,e.n=2,navigator.clipboard.writeText(t);case 2:return e.a(2);case 3:e.p=3,e.v;case 4:r=null!=i?i:document.body,(o=document.createElement("textarea")).value=t,r.appendChild(o),o.select(),document.execCommand("copy"),r.removeChild(o);case 5:return e.a(2)}}),e,null,[[1,3]])})));return function(t,i){return e.apply(this,arguments)}}()},16857:function(e,t,i){var a,r,o=i(44734),n=i(56038),s=i(69683),c=i(6454),d=i(25460),l=(i(28706),i(18111),i(7588),i(2892),i(26099),i(23500),i(62826)),h=i(96196),u=i(77845),p=i(76679),m=(i(41742),i(1554),e=>e),_=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).corner="BOTTOM_START",e.menuCorner="START",e.x=null,e.y=null,e.multi=!1,e.activatable=!1,e.disabled=!1,e.fixed=!1,e.noAnchor=!1,e}return(0,c.A)(t,e),(0,n.A)(t,[{key:"items",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.items}},{key:"selected",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.selected}},{key:"focus",value:function(){var e,t;null!==(e=this._menu)&&void 0!==e&&e.open?this._menu.focusItemAtIndex(0):null===(t=this._triggerButton)||void 0===t||t.focus()}},{key:"render",value:function(){return(0,h.qy)(a||(a=m`
      <div @click=${0}>
        <slot name="trigger" @slotchange=${0}></slot>
      </div>
      <ha-menu
        .corner=${0}
        .menuCorner=${0}
        .fixed=${0}
        .multi=${0}
        .activatable=${0}
        .y=${0}
        .x=${0}
      >
        <slot></slot>
      </ha-menu>
    `),this._handleClick,this._setTriggerAria,this.corner,this.menuCorner,this.fixed,this.multi,this.activatable,this.y,this.x)}},{key:"firstUpdated",value:function(e){(0,d.A)(t,"firstUpdated",this,3)([e]),"rtl"===p.G.document.dir&&this.updateComplete.then((()=>{this.querySelectorAll("ha-list-item").forEach((e=>{var t=document.createElement("style");t.innerHTML="span.material-icons:first-of-type { margin-left: var(--mdc-list-item-graphic-margin, 32px) !important; margin-right: 0px !important;}",e.shadowRoot.appendChild(t)}))}))}},{key:"_handleClick",value:function(){this.disabled||(this._menu.anchor=this.noAnchor?null:this,this._menu.show())}},{key:"_triggerButton",get:function(){return this.querySelector('ha-icon-button[slot="trigger"], ha-button[slot="trigger"]')}},{key:"_setTriggerAria",value:function(){this._triggerButton&&(this._triggerButton.ariaHasPopup="menu")}}])}(h.WF);_.styles=(0,h.AH)(r||(r=m`
    :host {
      display: inline-block;
      position: relative;
    }
    ::slotted([disabled]) {
      color: var(--disabled-text-color);
    }
  `)),(0,l.__decorate)([(0,u.MZ)()],_.prototype,"corner",void 0),(0,l.__decorate)([(0,u.MZ)({attribute:"menu-corner"})],_.prototype,"menuCorner",void 0),(0,l.__decorate)([(0,u.MZ)({type:Number})],_.prototype,"x",void 0),(0,l.__decorate)([(0,u.MZ)({type:Number})],_.prototype,"y",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"multi",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"activatable",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"fixed",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean,attribute:"no-anchor"})],_.prototype,"noAnchor",void 0),(0,l.__decorate)([(0,u.P)("ha-menu",!0)],_.prototype,"_menu",void 0),_=(0,l.__decorate)([(0,u.EM)("ha-button-menu")],_)},86451:function(e,t,i){var a,r,o,n,s,c,d=i(44734),l=i(56038),h=i(69683),u=i(6454),p=(i(28706),i(62826)),m=i(96196),_=i(77845),v=e=>e,g=function(e){function t(){var e;(0,d.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,h.A)(this,t,[].concat(a))).subtitlePosition="below",e.showBorder=!1,e}return(0,u.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){var e=(0,m.qy)(a||(a=v`<div class="header-title">
      <slot name="title"></slot>
    </div>`)),t=(0,m.qy)(r||(r=v`<div class="header-subtitle">
      <slot name="subtitle"></slot>
    </div>`));return(0,m.qy)(o||(o=v`
      <header class="header">
        <div class="header-bar">
          <section class="header-navigation-icon">
            <slot name="navigationIcon"></slot>
          </section>
          <section class="header-content">
            ${0}
          </section>
          <section class="header-action-items">
            <slot name="actionItems"></slot>
          </section>
        </div>
        <slot></slot>
      </header>
    `),"above"===this.subtitlePosition?(0,m.qy)(n||(n=v`${0}${0}`),t,e):(0,m.qy)(s||(s=v`${0}${0}`),e,t))}}],[{key:"styles",get:function(){return[(0,m.AH)(c||(c=v`
        :host {
          display: block;
        }
        :host([show-border]) {
          border-bottom: 1px solid
            var(--mdc-dialog-scroll-divider-color, rgba(0, 0, 0, 0.12));
        }
        .header-bar {
          display: flex;
          flex-direction: row;
          align-items: center;
          padding: 0 var(--ha-space-1);
          box-sizing: border-box;
        }
        .header-content {
          flex: 1;
          padding: 10px var(--ha-space-1);
          display: flex;
          flex-direction: column;
          justify-content: center;
          min-height: var(--ha-space-12);
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .header-title {
          height: var(
            --ha-dialog-header-title-height,
            calc(var(--ha-font-size-xl) + var(--ha-space-1))
          );
          font-size: var(--ha-font-size-xl);
          line-height: var(--ha-line-height-condensed);
          font-weight: var(--ha-font-weight-medium);
          color: var(--ha-dialog-header-title-color, var(--primary-text-color));
        }
        .header-subtitle {
          font-size: var(--ha-font-size-m);
          line-height: var(--ha-line-height-normal);
          color: var(
            --ha-dialog-header-subtitle-color,
            var(--secondary-text-color)
          );
        }
        @media all and (min-width: 450px) and (min-height: 500px) {
          .header-bar {
            padding: 0 var(--ha-space-2);
          }
        }
        .header-navigation-icon {
          flex: none;
          min-width: var(--ha-space-2);
          height: 100%;
          display: flex;
          flex-direction: row;
        }
        .header-action-items {
          flex: none;
          min-width: var(--ha-space-2);
          height: 100%;
          display: flex;
          flex-direction: row;
        }
      `))]}}])}(m.WF);(0,p.__decorate)([(0,_.MZ)({type:String,attribute:"subtitle-position"})],g.prototype,"subtitlePosition",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],g.prototype,"showBorder",void 0),g=(0,p.__decorate)([(0,_.EM)("ha-dialog-header")],g)},47806:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t);var r=i(61397),o=i(50264),n=i(44734),s=i(56038),c=i(69683),d=i(6454),l=(i(28706),i(34782),i(62826)),h=i(96196),u=i(77845),p=i(92542),m=i(55124),_=i(39396),v=(i(95637),i(86451),i(56565),i(74093)),g=i(16701),f=e([v,g]);[v,g]=f.then?(await f)():f;var y,b,w,x=e=>e,k=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(a)))._preferredLayout="auto",e}return(0,d.A)(t,e),(0,s.A)(t,[{key:"showDialog",value:function(e){this._params=e,this._navigateIds=e.navigateIds||[{media_content_id:void 0,media_content_type:void 0}]}},{key:"closeDialog",value:function(){this._params=void 0,this._navigateIds=void 0,this._currentItem=void 0,this._preferredLayout="auto",this.classList.remove("opened"),(0,p.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"render",value:function(){var e;return this._params&&this._navigateIds?(0,h.qy)(y||(y=x`
      <ha-dialog
        open
        scrimClickAction
        escapeKeyAction
        hideActions
        flexContent
        .heading=${0}
        @closed=${0}
        @opened=${0}
      >
        <ha-dialog-header show-border slot="heading">
          ${0}
          <span slot="title">
            ${0}
          </span>
          <ha-media-manage-button
            slot="actionItems"
            .hass=${0}
            .currentItem=${0}
            @media-refresh=${0}
          ></ha-media-manage-button>
          <ha-button-menu
            slot="actionItems"
            @action=${0}
            @closed=${0}
            fixed
          >
            <ha-icon-button
              slot="trigger"
              .label=${0}
              .path=${0}
            ></ha-icon-button>
            <ha-list-item graphic="icon">
              ${0}
              <ha-svg-icon
                class=${0}
                slot="graphic"
                .path=${0}
              ></ha-svg-icon>
            </ha-list-item>
            <ha-list-item graphic="icon">
              ${0}
              <ha-svg-icon
                class=${0}
                slot="graphic"
                .path=${0}
              ></ha-svg-icon>
            </ha-list-item>
            <ha-list-item graphic="icon">
              ${0}
              <ha-svg-icon
                slot="graphic"
                class=${0}
                .path=${0}
              ></ha-svg-icon>
            </ha-list-item>
          </ha-button-menu>
          <ha-icon-button
            .label=${0}
            .path=${0}
            dialogAction="close"
            slot="actionItems"
          ></ha-icon-button>
        </ha-dialog-header>
        <ha-media-player-browse
          dialog
          .hass=${0}
          .entityId=${0}
          .navigateIds=${0}
          .action=${0}
          .preferredLayout=${0}
          .accept=${0}
          .defaultId=${0}
          .defaultType=${0}
          .hideContentType=${0}
          .contentIdHelper=${0}
          @close-dialog=${0}
          @media-picked=${0}
          @media-browsed=${0}
        ></ha-media-player-browse>
      </ha-dialog>
    `),this._currentItem?this._currentItem.title:this.hass.localize("ui.components.media-browser.media-player-browser"),this.closeDialog,this._dialogOpened,this._navigateIds.length>(null!==(e=this._params.minimumNavigateLevel)&&void 0!==e?e:1)?(0,h.qy)(b||(b=x`
                <ha-icon-button
                  slot="navigationIcon"
                  .path=${0}
                  @click=${0}
                ></ha-icon-button>
              `),"M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z",this._goBack):h.s6,this._currentItem?this._currentItem.title:this.hass.localize("ui.components.media-browser.media-player-browser"),this.hass,this._currentItem,this._refreshMedia,this._handleMenuAction,m.d,this.hass.localize("ui.common.menu"),"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this.hass.localize("ui.components.media-browser.auto"),"auto"===this._preferredLayout?"selected_menu_item":"","M3,5A2,2 0 0,1 5,3H19A2,2 0 0,1 21,5V19A2,2 0 0,1 19,21H5C3.89,21 3,20.1 3,19V5M5,5V19H19V5H5M11,7H13A2,2 0 0,1 15,9V17H13V13H11V17H9V9A2,2 0 0,1 11,7M11,9V11H13V9H11Z",this.hass.localize("ui.components.media-browser.grid"),"grid"===this._preferredLayout?"selected_menu_item":"","M10,4V8H14V4H10M16,4V8H20V4H16M16,10V14H20V10H16M16,16V20H20V16H16M14,20V16H10V20H14M8,20V16H4V20H8M8,14V10H4V14H8M8,8V4H4V8H8M10,14H14V10H10V14M4,2H20A2,2 0 0,1 22,4V20A2,2 0 0,1 20,22H4C2.92,22 2,21.1 2,20V4A2,2 0 0,1 4,2Z",this.hass.localize("ui.components.media-browser.list"),"list"===this._preferredLayout?"selected_menu_item":"","M11 15H17V17H11V15M9 7H7V9H9V7M11 13H17V11H11V13M11 9H17V7H11V9M9 11H7V13H9V11M21 5V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H19C20.1 3 21 3.9 21 5M19 5H5V19H19V5M9 15H7V17H9V15Z",this.hass.localize("ui.common.close"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",this.hass,this._params.entityId,this._navigateIds,this._action,this._preferredLayout,this._params.accept,this._params.defaultId,this._params.defaultType,this._params.hideContentType,this._params.contentIdHelper,this.closeDialog,this._mediaPicked,this._mediaBrowsed):h.s6}},{key:"_dialogOpened",value:function(){this.classList.add("opened")}},{key:"_handleMenuAction",value:(i=(0,o.A)((0,r.A)().m((function e(t){var i;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:i=t.detail.index,e.n=0===i?1:1===i?2:2===i?3:4;break;case 1:return this._preferredLayout="auto",e.a(3,4);case 2:return this._preferredLayout="grid",e.a(3,4);case 3:return this._preferredLayout="list",e.a(3,4);case 4:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_goBack",value:function(){var e;this._navigateIds=null===(e=this._navigateIds)||void 0===e?void 0:e.slice(0,-1),this._currentItem=void 0}},{key:"_mediaBrowsed",value:function(e){this._navigateIds=e.detail.ids,this._currentItem=e.detail.current}},{key:"_mediaPicked",value:function(e){this._params.mediaPickedCallback(e.detail),"play"!==this._action&&this.closeDialog()}},{key:"_action",get:function(){return this._params.action||"play"}},{key:"_refreshMedia",value:function(){this._browser.refresh()}}],[{key:"styles",get:function(){return[_.nA,_.kO,(0,h.AH)(w||(w=x`
        ha-dialog {
          --dialog-z-index: 9;
          --dialog-content-padding: 0;
        }

        ha-media-player-browse {
          --media-browser-max-height: calc(
            100vh - 65px - var(--safe-area-inset-y)
          );
        }

        :host(.opened) ha-media-player-browse {
          height: calc(100vh - 65px - var(--safe-area-inset-y));
        }

        @media (min-width: 800px) {
          ha-dialog {
            --mdc-dialog-max-width: 800px;
            --mdc-dialog-max-height: calc(
              100vh - var(--ha-space-18) - var(--safe-area-inset-y)
            );
          }
          ha-media-player-browse {
            position: initial;
            --media-browser-max-height: calc(
              100vh - 145px - var(--safe-area-inset-y)
            );
            width: 700px;
          }
        }

        ha-dialog-header ha-media-manage-button {
          --mdc-theme-primary: var(--primary-text-color);
          margin: 6px;
          display: block;
        }
      `))]}}]);var i}(h.WF);(0,l.__decorate)([(0,u.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,l.__decorate)([(0,u.wk)()],k.prototype,"_currentItem",void 0),(0,l.__decorate)([(0,u.wk)()],k.prototype,"_navigateIds",void 0),(0,l.__decorate)([(0,u.wk)()],k.prototype,"_params",void 0),(0,l.__decorate)([(0,u.wk)()],k.prototype,"_preferredLayout",void 0),(0,l.__decorate)([(0,u.P)("ha-media-player-browse")],k.prototype,"_browser",void 0),k=(0,l.__decorate)([(0,u.EM)("dialog-media-player-browse")],k),a()}catch($){a($)}}))},75090:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(94741),r=i(44734),o=i(56038),n=i(69683),s=i(6454),c=(i(28706),i(62826)),d=i(96196),l=i(77845),h=i(22786),u=i(92542),p=i(89473),m=(i(95379),i(91120),e([p]));p=(m.then?(await m)():m)[0];var _,v,g=e=>e,f=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).hideContentType=!1,e._schema=(0,h.A)((e=>[{name:"media_content_id",required:!0,selector:{text:{}}}].concat((0,a.A)(e?[]:[{name:"media_content_type",required:!1,selector:{text:{}}}])))),e._computeLabel=t=>{switch(t.name){case"media_content_id":case"media_content_type":return e.hass.localize(`ui.components.selectors.media.${t.name}`)}return t.name},e._computeHelper=t=>{switch(t.name){case"media_content_id":return e.contentIdHelper||e.hass.localize(`ui.components.selectors.media.${t.name}_detail`);case"media_content_type":return e.hass.localize(`ui.components.selectors.media.${t.name}_detail`)}return""},e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){return(0,d.qy)(_||(_=g`
      <ha-card>
        <div class="card-content">
          <ha-form
            .hass=${0}
            .schema=${0}
            .data=${0}
            .computeLabel=${0}
            .computeHelper=${0}
            @value-changed=${0}
          ></ha-form>
        </div>
        <div class="card-actions">
          <ha-button @click=${0}>
            ${0}
          </ha-button>
        </div>
      </ha-card>
    `),this.hass,this._schema(this.hideContentType),this.item,this._computeLabel,this._computeHelper,this._valueChanged,this._mediaPicked,this.hass.localize("ui.common.submit"))}},{key:"_valueChanged",value:function(e){var t=Object.assign({},e.detail.value);this.item=t}},{key:"_mediaPicked",value:function(){(0,u.r)(this,"manual-media-picked",{item:{media_content_id:this.item.media_content_id||"",media_content_type:this.item.media_content_type||""}})}}])}(d.WF);f.styles=(0,d.AH)(v||(v=g`
    :host {
      margin: 16px auto;
      padding: 0 8px;
      display: flex;
      flex-direction: column;
      max-width: 448px;
    }
    .card-actions {
      display: flex;
      justify-content: flex-end;
    }
  `)),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],f.prototype,"item",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],f.prototype,"hideContentType",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],f.prototype,"contentIdHelper",void 0),f=(0,c.__decorate)([(0,l.EM)("ha-browse-media-manual")],f),t()}catch(y){t(y)}}))},59939:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),o=i(44734),n=i(56038),s=i(69683),c=i(25460),d=i(6454),l=(i(50113),i(23792),i(18111),i(20116),i(26099),i(38781),i(62953),i(48408),i(14603),i(47566),i(98721),i(62826)),h=i(96196),u=i(77845),p=i(42256),m=i(92542),_=i(4657),v=i(71750),g=i(62146),f=i(39396),y=i(4848),b=i(89473),w=(i(95379),i(51362)),x=(i(67591),i(10054),e([b,w]));[b,w]=x.then?(await x)():x;var k,$,A,H,z=e=>e,I=function(e){function t(){return(0,o.A)(this,t),(0,s.A)(this,t,arguments)}return(0,d.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e,t;return(0,h.qy)(k||(k=z`
      <ha-card>
        <div class="card-content">
          <ha-textarea
            autogrow
            .label=${0}
            .value=${0}
          >
          </ha-textarea>
          ${0}
        </div>
        <div class="card-actions">
          <ha-button appearance="plain" @click=${0}>
            ${0}
          </ha-button>
        </div>
      </ha-card>
      ${0}
    `),this.hass.localize("ui.components.media-browser.tts.message"),this._message||this.hass.localize("ui.components.media-browser.tts.example_message",{name:(null===(e=this.hass.user)||void 0===e?void 0:e.name)||"Alice"}),null!==(t=this._provider)&&void 0!==t&&null!==(t=t.supported_languages)&&void 0!==t&&t.length?(0,h.qy)($||($=z` <div class="options">
                <ha-language-picker
                  .hass=${0}
                  .languages=${0}
                  .value=${0}
                  required
                  @value-changed=${0}
                ></ha-language-picker>
                <ha-tts-voice-picker
                  .hass=${0}
                  .value=${0}
                  .engineId=${0}
                  .language=${0}
                  required
                  @value-changed=${0}
                ></ha-tts-voice-picker>
              </div>`),this.hass,this._provider.supported_languages,this._language,this._languageChanged,this.hass,this._voice,this._provider.engine_id,this._language,this._voiceChanged):h.s6,this._ttsClicked,this.hass.localize(`ui.components.media-browser.tts.action_${this.action}`),this._voice?(0,h.qy)(A||(A=z`
            <div class="footer">
              ${0}
              <code>${0}</code>
              <ha-icon-button
                .path=${0}
                @click=${0}
                title=${0}
              ></ha-icon-button>
            </div>
          `),this.hass.localize("ui.components.media-browser.tts.selected_voice_id"),this._voice||"-","M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z",this._copyVoiceId,this.hass.localize("ui.components.media-browser.tts.copy_voice_id")):h.s6)}},{key:"willUpdate",value:function(e){var i;if((0,c.A)(t,"willUpdate",this,3)([e]),e.has("item")&&this.item.media_content_id){var a,r=new URLSearchParams(this.item.media_content_id.split("?")[1]),o=r.get("message"),n=r.get("language"),s=r.get("voice");o&&(this._message=o),n&&(this._language=n),s&&(this._voice=s);var d=(0,g.EF)(this.item.media_content_id);d!==(null===(a=this._provider)||void 0===a?void 0:a.engine_id)&&(this._provider=void 0,(0,g.u1)(this.hass,d).then((e=>{var t;if(this._provider=e.provider,!this._language&&null!==(t=e.provider.supported_languages)&&void 0!==t&&t.length){var i,a=`${this.hass.config.language}-${this.hass.config.country}`.toLowerCase(),r=e.provider.supported_languages.find((e=>e.toLowerCase()===a));if(r)return void(this._language=r);this._language=null===(i=e.provider.supported_languages)||void 0===i?void 0:i.find((e=>e.substring(0,2)===this.hass.config.language.substring(0,2)))}})),"cloud"===d&&(0,v.eN)(this.hass).then((e=>{e.logged_in&&(this._language=e.prefs.tts_default_voice[0])})))}if(!e.has("_message")){var l=null===(i=this.shadowRoot.querySelector("ha-textarea"))||void 0===i?void 0:i.value;void 0!==l&&l!==this._message&&(this._message=l)}}},{key:"_languageChanged",value:function(e){this._language=e.detail.value}},{key:"_voiceChanged",value:function(e){this._voice=e.detail.value}},{key:"_ttsClicked",value:(l=(0,r.A)((0,a.A)().m((function e(){var t,i,r;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:t=this.shadowRoot.querySelector("ha-textarea").value,this._message=t,i=Object.assign({},this.item),(r=new URLSearchParams).append("message",t),this._language&&r.append("language",this._language),this._voice&&r.append("voice",this._voice),i.media_content_id=`${i.media_content_id.split("?")[0]}?${r.toString()}`,i.media_content_type="audio/mp3",i.can_play=!0,i.title=t,(0,m.r)(this,"tts-picked",{item:i});case 1:return e.a(2)}}),e,this)}))),function(){return l.apply(this,arguments)})},{key:"_copyVoiceId",value:(i=(0,r.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return t.preventDefault(),e.n=1,(0,_.l)(this._voice);case 1:(0,y.P)(this,{message:this.hass.localize("ui.common.copied_clipboard")});case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}]);var i,l}(h.WF);I.styles=[f.og,(0,h.AH)(H||(H=z`
      :host {
        margin: 16px auto;
        padding: 0 8px;
        display: flex;
        flex-direction: column;
        max-width: 448px;
      }
      .options {
        margin-top: 16px;
        display: flex;
        justify-content: space-between;
      }
      ha-textarea {
        width: 100%;
      }
      button.link {
        color: var(--primary-color);
      }
      .footer {
        font-size: var(--ha-font-size-s);
        color: var(--secondary-text-color);
        margin: 16px 0;
        text-align: center;
      }
      .footer code {
        font-weight: var(--ha-font-weight-bold);
      }
      .footer {
        --mdc-icon-size: 14px;
        --mdc-icon-button-size: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 6px;
      }
    `))],(0,l.__decorate)([(0,u.MZ)({attribute:!1})],I.prototype,"hass",void 0),(0,l.__decorate)([(0,u.MZ)({attribute:!1})],I.prototype,"item",void 0),(0,l.__decorate)([(0,u.MZ)()],I.prototype,"action",void 0),(0,l.__decorate)([(0,u.wk)()],I.prototype,"_language",void 0),(0,l.__decorate)([(0,u.wk)()],I.prototype,"_voice",void 0),(0,l.__decorate)([(0,u.wk)()],I.prototype,"_provider",void 0),(0,l.__decorate)([(0,u.wk)(),(0,p.I)({key:"TtsMessage",state:!0,subscribe:!1})],I.prototype,"_message",void 0),I=(0,l.__decorate)([(0,u.EM)("ha-browse-media-tts")],I),t()}catch(M){t(M)}}))},74093:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=(i(28706),i(62826)),c=i(96196),d=i(77845),l=i(92542),h=i(9923),u=(i(60961),i(89473)),p=i(76019),m=e([u]);u=(m.then?(await m)():m)[0];var _,v=e=>e,g=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),n=0;n<i;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r)))._uploading=0,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e;return this.currentItem&&((0,h.Jz)(this.currentItem.media_content_id||"")||null!==(e=this.hass.user)&&void 0!==e&&e.is_admin&&(0,h.iY)(this.currentItem.media_content_id))?(0,c.qy)(_||(_=v`
      <ha-button appearance="filled" size="small" @click=${0}>
        <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
        ${0}
      </ha-button>
    `),this._manage,"M19.39 10.74L11 19.13V20H4C2.9 20 2 19.11 2 18V6C2 4.89 2.89 4 4 4H10L12 6H20C21.1 6 22 6.89 22 8V10.15C21.74 10.06 21.46 10 21.17 10C20.5 10 19.87 10.26 19.39 10.74M13 19.96V22H15.04L21.17 15.88L19.13 13.83L13 19.96M22.85 13.47L21.53 12.15C21.33 11.95 21 11.95 20.81 12.15L19.83 13.13L21.87 15.17L22.85 14.19C23.05 14 23.05 13.67 22.85 13.47Z",this.hass.localize("ui.components.media-browser.file_management.manage")):c.s6}},{key:"_manage",value:function(){(0,p.l)(this,{currentItem:this.currentItem,onClose:()=>(0,l.r)(this,"media-refresh")})}}])}(c.WF);(0,s.__decorate)([(0,d.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],g.prototype,"currentItem",void 0),(0,s.__decorate)([(0,d.wk)()],g.prototype,"_uploading",void 0),g=(0,s.__decorate)([(0,d.EM)("ha-media-manage-button")],g),t()}catch(f){t(f)}}))},16701:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(31432),r=i(61397),o=i(94741),n=i(50264),s=i(44734),c=i(56038),d=i(75864),l=i(69683),h=i(6454),u=i(25460),p=i(71950),m=(i(28706),i(2008),i(74423),i(23792),i(44114),i(34782),i(18111),i(81148),i(22489),i(13579),i(26099),i(3362),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(62953),i(62826)),_=i(52920),v=i(96196),g=i(77845),f=i(94333),y=i(29485),b=i(45847),w=i(92542),x=i(93777),k=i(40404),$=i(31136),A=i(92001),H=i(9923),z=i(62146),I=i(10234),M=i(39396),V=i(84183),C=i(76681),L=i(62001),q=i(82965),Z=(i(17963),i(89473)),T=(i(16857),i(95379),i(70748),i(60733),i(75261),i(56565),i(89600)),E=(i(60961),i(88422)),O=i(75090),P=i(59939),S=e([p,q,Z,T,E,O,P]);[p,q,Z,T,E,O,P]=S.then?(await S)():S;var B,U,R,W,j,F,D,N,Y,J,K,G,X,Q,ee,te,ie,ae,re,oe,ne,se,ce,de,le,he,ue,pe,me,_e=e=>e,ve="M8,5.14V19.14L19,12.14L8,5.14Z",ge="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",fe={can_expand:!0,can_play:!1,can_search:!1,children_media_class:"",media_class:"app",media_content_id:H.xw,media_content_type:"",iconPath:"M19,10H17V8H19M19,13H17V11H19M16,10H14V8H16M16,13H14V11H16M16,17H8V15H16M7,10H5V8H7M7,13H5V11H7M8,11H10V13H8M8,8H10V10H8M11,11H13V13H11M11,8H13V10H11M20,5H4C2.89,5 2,5.89 2,7V17A2,2 0 0,0 4,19H20A2,2 0 0,0 22,17V7C22,5.89 21.1,5 20,5Z",title:"Manual entry"},ye=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),c=0;c<i;c++)a[c]=arguments[c];return(e=(0,l.A)(this,t,[].concat(a))).action="play",e.preferredLayout="auto",e.dialog=!1,e.navigateIds=[],e.hideContentType=!1,e.narrow=!1,e.scrolled=!1,e._observed=!1,e._headerOffsetHeight=0,e._renderGridItem=t=>{var i=t.thumbnail?e._getThumbnailURLorBase64(t.thumbnail).then((e=>`url(${e})`)):"none";return(0,v.qy)(B||(B=_e`
      <div class="child" .item=${0} @click=${0}>
        <ha-card outlined>
          <div class="thumbnail">
            ${0}
            ${0}
          </div>
          <ha-tooltip .for="grid-${0}" distance="-4">
            ${0}
          </ha-tooltip>
          <div .id="grid-${0}" class="title">
            ${0}
          </div>
        </ha-card>
      </div>
    `),t,e._childClicked,t.thumbnail?(0,v.qy)(U||(U=_e`
                  <div
                    class="${0} image"
                    style="background-image: ${0}"
                  ></div>
                `),(0,f.H)({"centered-image":["app","directory"].includes(t.media_class),"brand-image":(0,C.bg)(t.thumbnail)}),(0,b.T)(i,"")):(0,v.qy)(R||(R=_e`
                  <div class="icon-holder image">
                    <ha-svg-icon
                      class=${0}
                      .path=${0}
                    ></ha-svg-icon>
                  </div>
                `),t.iconPath?"icon":"folder",t.iconPath||A.EC["directory"===t.media_class&&t.children_media_class||t.media_class].icon),t.can_play?(0,v.qy)(W||(W=_e`
                  <ha-icon-button
                    class="play ${0}"
                    .item=${0}
                    .label=${0}
                    .path=${0}
                    @click=${0}
                  ></ha-icon-button>
                `),(0,f.H)({can_expand:t.can_expand}),t,e.hass.localize(`ui.components.media-browser.${e.action}-media`),"play"===e.action?ve:ge,e._actionClicked):"",(0,x.Y)(t.title),t.title,(0,x.Y)(t.title),t.title)},e._renderListItem=t=>{var i=e._currentItem,a=A.EC[i.media_class],r=a.show_list_images&&t.thumbnail?e._getThumbnailURLorBase64(t.thumbnail).then((e=>`url(${e})`)):"none";return(0,v.qy)(j||(j=_e`
      <ha-list-item
        @click=${0}
        .item=${0}
        .graphic=${0}
      >
        ${0}
        <span class="title">${0}</span>
      </ha-list-item>
    `),e._childClicked,t,a.show_list_images?"medium":"avatar","none"!==r||t.can_play?(0,v.qy)(D||(D=_e`<div
              class=${0}
              style="background-image: ${0}"
              slot="graphic"
            >
              ${0}
            </div>`),(0,f.H)({graphic:!0,thumbnail:!0===a.show_list_images}),(0,b.T)(r,""),t.can_play?(0,v.qy)(N||(N=_e`<ha-icon-button
                    class="play ${0}"
                    .item=${0}
                    .label=${0}
                    .path=${0}
                    @click=${0}
                  ></ha-icon-button>`),(0,f.H)({show:!a.show_list_images||!t.thumbnail}),t,e.hass.localize(`ui.components.media-browser.${e.action}-media`),"play"===e.action?ve:ge,e._actionClicked):v.s6):(0,v.qy)(F||(F=_e`<ha-svg-icon
              .path=${0}
              slot="graphic"
            ></ha-svg-icon>`),A.EC["directory"===t.media_class&&t.children_media_class||t.media_class].icon),t.title)},e._actionClicked=t=>{t.stopPropagation();var i=t.currentTarget.item;e._runAction(i)},e._childClicked=function(){var t=(0,n.A)((0,r.A)().m((function t(i){var a,n;return(0,r.A)().w((function(t){for(;;)switch(t.n){case 0:if(a=i.currentTarget,n=a.item){t.n=1;break}return t.a(2);case 1:if(n.can_expand){t.n=2;break}return e._runAction(n),t.a(2);case 2:(0,w.r)((0,d.A)(e),"media-browsed",{ids:[].concat((0,o.A)(e.navigateIds),[n])});case 3:return t.a(2)}}),t)})));return function(e){return t.apply(this,arguments)}}(),e}return(0,h.A)(t,e),(0,c.A)(t,[{key:"connectedCallback",value:function(){(0,u.A)(t,"connectedCallback",this,3)([]),this.updateComplete.then((()=>this._attachResizeObserver()))}},{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._resizeObserver&&this._resizeObserver.disconnect()}},{key:"refresh",value:(q=(0,n.A)((0,r.A)().m((function e(){var t,i;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return t=this.navigateIds[this.navigateIds.length-1],e.p=1,e.n=2,this._fetchData(this.entityId,t.media_content_id,t.media_content_type);case 2:this._currentItem=e.v,(0,w.r)(this,"media-browsed",{ids:this.navigateIds,current:this._currentItem}),e.n=4;break;case 3:e.p=3,i=e.v,this._setError(i);case 4:return e.a(2)}}),e,this,[[1,3]])}))),function(){return q.apply(this,arguments)})},{key:"play",value:function(){var e;null!==(e=this._currentItem)&&void 0!==e&&e.can_play&&this._runAction(this._currentItem)}},{key:"willUpdate",value:function(e){var i;if((0,u.A)(t,"willUpdate",this,3)([e]),this.hasUpdated||(0,V.i)(),e.has("entityId"))this._setError(void 0);else if(!e.has("navigateIds"))return;this._setError(void 0);var a=e.get("navigateIds"),r=this.navigateIds;null===(i=this._content)||void 0===i||i.scrollTo(0,0),this.scrolled=!1;var o=this._currentItem,n=this._parentItem;this._currentItem=void 0,this._parentItem=void 0;var s,c,d=r[r.length-1],l=r.length>1?r[r.length-2]:void 0;e.has("entityId")||(a&&r.length===a.length+1&&a.every(((e,t)=>{var i=r[t];return i.media_content_id===e.media_content_id&&i.media_content_type===e.media_content_type}))?c=Promise.resolve(o):a&&r.length===a.length-1&&r.every(((e,t)=>{var i=a[t];return e.media_content_id===i.media_content_id&&e.media_content_type===i.media_content_type}))&&(s=Promise.resolve(n))),d.media_content_id&&(0,H.CY)(d.media_content_id)?(this._currentItem=fe,(0,w.r)(this,"media-browsed",{ids:r,current:this._currentItem})):(s||(s=this._fetchData(this.entityId,d.media_content_id,d.media_content_type)),s.then((e=>{this._currentItem=e,(0,w.r)(this,"media-browsed",{ids:r,current:e})}),(t=>{var i;a&&e.has("entityId")&&r.length===a.length&&a.every(((e,t)=>r[t].media_content_id===e.media_content_id&&r[t].media_content_type===e.media_content_type))?(0,w.r)(this,"media-browsed",{ids:[{media_content_id:void 0,media_content_type:void 0}],replace:!0}):"entity_not_found"===t.code&&this.entityId&&(0,$.g0)(null===(i=this.hass.states[this.entityId])||void 0===i?void 0:i.state)?this._setError({message:this.hass.localize("ui.components.media-browser.media_player_unavailable"),code:"entity_not_found"}):this._setError(t)}))),c||void 0===l||(c=this._fetchData(this.entityId,l.media_content_id,l.media_content_type)),c&&c.then((e=>{this._parentItem=e}))}},{key:"shouldUpdate",value:function(e){if(e.size>1||!e.has("hass"))return!0;var t=e.get("hass");return void 0===t||t.localize!==this.hass.localize}},{key:"firstUpdated",value:function(){this._measureCard(),this._attachResizeObserver()}},{key:"updated",value:function(e){if((0,u.A)(t,"updated",this,3)([e]),e.has("_scrolled"))this._animateHeaderHeight();else if(e.has("_currentItem")){var i;if(this._setHeaderHeight(),this._observed)return;var a=null===(i=this._virtualizer)||void 0===i?void 0:i._virtualizer;a&&(this._observed=!0,setTimeout((()=>a._observeMutations()),0))}}},{key:"render",value:function(){if(this._error)return(0,v.qy)(Y||(Y=_e`
        <div class="container">
          <ha-alert alert-type="error">
            ${0}
          </ha-alert>
        </div>
      `),this._renderError(this._error));if(!this._currentItem)return(0,v.qy)(J||(J=_e`<ha-spinner></ha-spinner>`));var e=this._currentItem,t=this.hass.localize(`ui.components.media-browser.class.${e.media_class}`),i=e.children||[],r=new Set;if(this.accept&&i.length>0){var o,n=[],s=(0,a.A)(this.accept);try{var c=function(){var e=o.value;if(e.endsWith("/*")){var t=e.slice(0,-1);n.push((e=>e.startsWith(t)))}else{if("*"===e)return n=[()=>!0],1;n.push((t=>t===e))}};for(s.s();!(o=s.n()).done&&!c(););}catch(u){s.e(u)}finally{s.f()}i=i.filter((e=>{var t=e.media_content_type.toLowerCase(),i=e.media_content_type&&n.some((e=>e(t)));return i&&r.add(e.media_content_id),!e.media_content_type||e.can_expand||i}))}var d=A.EC[e.media_class],l=e.children_media_class?A.EC[e.children_media_class]:A.EC.directory,h=e.thumbnail?this._getThumbnailURLorBase64(e.thumbnail).then((e=>`url(${e})`)):"none";return(0,v.qy)(K||(K=_e`
              ${0}
          <div
            class="content"
            @scroll=${0}
            @touchmove=${0}
          >
            ${0}
          </div>
        </div>
      </div>
    `),e.can_play?(0,v.qy)(G||(G=_e`
                      <div
                        class="header ${0}"
                        @transitionend=${0}
                      >
                        <div class="header-content">
                          ${0}
                          <div class="header-info">
                            <div class="breadcrumb">
                              <h1 class="title">${0}</h1>
                              ${0}
                            </div>
                            ${0}
                          </div>
                        </div>
                      </div>
                    `),(0,f.H)({"no-img":!e.thumbnail,"no-dialog":!this.dialog}),this._setHeaderHeight,e.thumbnail?(0,v.qy)(X||(X=_e`
                                <div
                                  class="img"
                                  style="background-image: ${0}"
                                >
                                  ${0}
                                </div>
                              `),(0,b.T)(h,""),this.narrow&&null!=e&&e.can_play&&(!this.accept||r.has(e.media_content_id))?(0,v.qy)(Q||(Q=_e`
                                        <ha-fab
                                          mini
                                          .item=${0}
                                          @click=${0}
                                        >
                                          <ha-svg-icon
                                            slot="icon"
                                            .label=${0}
                                            .path=${0}
                                          ></ha-svg-icon>
                                          ${0}
                                        </ha-fab>
                                      `),e,this._actionClicked,this.hass.localize(`ui.components.media-browser.${this.action}-media`),"play"===this.action?ve:ge,this.hass.localize(`ui.components.media-browser.${this.action}`)):""):v.s6,e.title,t?(0,v.qy)(ee||(ee=_e` <h2 class="subtitle">${0}</h2> `),t):"",!e.can_play||e.thumbnail&&this.narrow?"":(0,v.qy)(te||(te=_e`
                                  <ha-button
                                    .item=${0}
                                    @click=${0}
                                  >
                                    <ha-svg-icon
                                      .label=${0}
                                      .path=${0}
                                      slot="start"
                                    ></ha-svg-icon>
                                    ${0}
                                  </ha-button>
                                `),e,this._actionClicked,this.hass.localize(`ui.components.media-browser.${this.action}-media`),"play"===this.action?ve:ge,this.hass.localize(`ui.components.media-browser.${this.action}`))):"",this._scroll,this._scroll,this._error?(0,v.qy)(ie||(ie=_e`
                    <div class="container">
                      <ha-alert alert-type="error">
                        ${0}
                      </ha-alert>
                    </div>
                  `),this._renderError(this._error)):(0,H.CY)(e.media_content_id)?(0,v.qy)(ae||(ae=_e`<ha-browse-media-manual
                      .item=${0}
                      .hass=${0}
                      .hideContentType=${0}
                      .contentIdHelper=${0}
                      @manual-media-picked=${0}
                    ></ha-browse-media-manual>`),{media_content_id:this.defaultId||"",media_content_type:this.defaultType||""},this.hass,this.hideContentType,this.contentIdHelper,this._manualPicked):(0,z.ni)(e.media_content_id)?(0,v.qy)(re||(re=_e`
                        <ha-browse-media-tts
                          .item=${0}
                          .hass=${0}
                          .action=${0}
                          @tts-picked=${0}
                        ></ha-browse-media-tts>
                      `),e,this.hass,this.action,this._ttsPicked):i.length||e.not_shown?"grid"===this.preferredLayout||"auto"===this.preferredLayout&&"grid"===l.layout?(0,v.qy)(se||(se=_e`
                            <lit-virtualizer
                              scroller
                              .layout=${0}
                              .items=${0}
                              .renderItem=${0}
                              class="children ${0}"
                            ></lit-virtualizer>
                            ${0}
                          `),(0,_.V)({itemSize:{width:"175px",height:"portrait"===l.thumbnail_ratio?"312px":"225px"},gap:"16px",flex:{preserve:"aspect-ratio"},justify:"space-evenly",direction:"vertical"}),i,this._renderGridItem,(0,f.H)({portrait:"portrait"===l.thumbnail_ratio,not_shown:!!e.not_shown}),e.not_shown?(0,v.qy)(ce||(ce=_e`
                                  <div class="grid not-shown">
                                    <div class="title">
                                      ${0}
                                    </div>
                                  </div>
                                `),this.hass.localize("ui.components.media-browser.not_shown",{count:e.not_shown})):""):(0,v.qy)(de||(de=_e`
                            <ha-list>
                              <lit-virtualizer
                                scroller
                                .items=${0}
                                style=${0}
                                .renderItem=${0}
                              ></lit-virtualizer>
                              ${0}
                            </ha-list>
                          `),i,(0,y.W)({height:72*i.length+26+"px"}),this._renderListItem,e.not_shown?(0,v.qy)(le||(le=_e`
                                    <ha-list-item
                                      noninteractive
                                      class="not-shown"
                                      .graphic=${0}
                                    >
                                      <span class="title">
                                        ${0}
                                      </span>
                                    </ha-list-item>
                                  `),d.show_list_images?"medium":"avatar",this.hass.localize("ui.components.media-browser.not_shown",{count:e.not_shown})):""):(0,v.qy)(oe||(oe=_e`
                          <div class="container no-items">
                            ${0}
                          </div>
                        `),"media-source://media_source/local/."===e.media_content_id?(0,v.qy)(ne||(ne=_e`
                                  <div class="highlight-add-button">
                                    <span>
                                      <ha-svg-icon
                                        .path=${0}
                                      ></ha-svg-icon>
                                    </span>
                                    <span>
                                      ${0}
                                    </span>
                                  </div>
                                `),"M21.5 9.5L20.09 10.92L17 7.83V13.5C17 17.09 14.09 20 10.5 20H4V18H10.5C13 18 15 16 15 13.5V7.83L11.91 10.91L10.5 9.5L16 4L21.5 9.5Z",this.hass.localize("ui.components.media-browser.file_management.highlight_button")):this.hass.localize("ui.components.media-browser.no_items")))}},{key:"_getThumbnailURLorBase64",value:(g=(0,n.A)((0,r.A)().m((function e(t){var i;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(t){e.n=1;break}return e.a(2,"");case 1:if(!t.startsWith("/")){e.n=2;break}return e.a(2,new Promise(((e,i)=>{this.hass.fetchWithAuth(t).then((e=>e.blob())).then((t=>{var a=new FileReader;a.onload=()=>{var t=a.result;e("string"==typeof t?t:"")},a.onerror=e=>i(e),a.readAsDataURL(t)}))})));case 2:return(0,C.bg)(t)&&(t=(0,C.MR)({domain:(0,C.a_)(t),type:"icon",useFallback:!0,darkOptimized:null===(i=this.hass.themes)||void 0===i?void 0:i.darkMode})),e.a(2,t)}}),e,this)}))),function(e){return g.apply(this,arguments)})},{key:"_runAction",value:function(e){(0,w.r)(this,"media-picked",{item:e,navigateIds:this.navigateIds})}},{key:"_ttsPicked",value:function(e){e.stopPropagation();var t=this.navigateIds.slice(0,-1);t.push(e.detail.item),(0,w.r)(this,"media-picked",Object.assign(Object.assign({},e.detail),{},{navigateIds:t}))}},{key:"_manualPicked",value:function(e){e.stopPropagation(),(0,w.r)(this,"media-picked",{item:e.detail.item,navigateIds:this.navigateIds})}},{key:"_fetchData",value:(m=(0,n.A)((0,r.A)().m((function e(t,i,a){var o;return(0,r.A)().w((function(e){for(;;)if(0===e.n)return o=t&&t!==A.H1?(0,A.ET)(this.hass,t,i,a):(0,H.Fn)(this.hass,i),e.a(2,o.then((e=>(i||"pick"!==this.action||(e.children=e.children||[],e.children.push(fe)),e))))}),e,this)}))),function(e,t,i){return m.apply(this,arguments)})},{key:"_measureCard",value:function(){this.narrow=(this.dialog?window.innerWidth:this.offsetWidth)<450}},{key:"_attachResizeObserver",value:(p=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:this._resizeObserver||(this._resizeObserver=new ResizeObserver((0,k.s)((()=>this._measureCard()),250,!1))),this._resizeObserver.observe(this);case 1:return e.a(2)}}),e,this)}))),function(){return p.apply(this,arguments)})},{key:"_closeDialogAction",value:function(){(0,w.r)(this,"close-dialog")}},{key:"_setError",value:function(e){this.dialog?e&&(this._closeDialogAction(),(0,I.K$)(this,{title:this.hass.localize("ui.components.media-browser.media_browsing_error"),text:this._renderError(e)})):this._error=e}},{key:"_renderError",value:function(e){return"Media directory does not exist."===e.message?(0,v.qy)(he||(he=_e`
        <h2>
          ${0}
        </h2>
        <p>
          ${0}
          <br />
          ${0}
          <br />
          ${0}
        </p>
      `),this.hass.localize("ui.components.media-browser.no_local_media_found"),this.hass.localize("ui.components.media-browser.no_media_folder"),this.hass.localize("ui.components.media-browser.setup_local_help",{documentation:(0,v.qy)(ue||(ue=_e`<a
              href=${0}
              target="_blank"
              rel="noreferrer"
              >${0}</a
            >`),(0,L.o)(this.hass,"/more-info/local-media/setup-media"),this.hass.localize("ui.components.media-browser.documentation"))}),this.hass.localize("ui.components.media-browser.local_media_files")):(0,v.qy)(pe||(pe=_e`<span class="error">${0}</span>`),e.message)}},{key:"_setHeaderHeight",value:(i=(0,n.A)((0,r.A)().m((function e(){var t,i;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:if(t=this._header,i=this._content,t&&i){e.n=2;break}return e.a(2);case 2:this._headerOffsetHeight=t.offsetHeight,i.style.marginTop=`${this._headerOffsetHeight}px`,i.style.maxHeight=`calc(var(--media-browser-max-height, 100%) - ${this._headerOffsetHeight}px)`;case 3:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_animateHeaderHeight",value:function(){var e,t=i=>{void 0===e&&(e=i);var a=i-e;this._setHeaderHeight(),a<400&&requestAnimationFrame(t)};requestAnimationFrame(t)}},{key:"_scroll",value:function(e){var t=e.currentTarget;!this.scrolled&&t.scrollTop>this._headerOffsetHeight?this.scrolled=!0:this.scrolled&&t.scrollTop<this._headerOffsetHeight&&(this.scrolled=!1)}}],[{key:"styles",get:function(){return[M.RF,(0,v.AH)(me||(me=_e`
        :host {
          display: flex;
          flex-direction: column;
          position: relative;
          direction: ltr;
        }

        ha-spinner {
          margin: 40px auto;
        }

        .container {
          padding: 16px;
        }

        .no-items {
          padding-left: 32px;
        }

        .highlight-add-button {
          display: flex;
          flex-direction: row-reverse;
          margin-right: 48px;
          margin-inline-end: 48px;
          margin-inline-start: initial;
          direction: var(--direction);
        }

        .highlight-add-button ha-svg-icon {
          position: relative;
          top: -0.5em;
          margin-left: 8px;
          margin-inline-start: 8px;
          margin-inline-end: initial;
          transform: scaleX(var(--scale-direction));
        }

        .content {
          overflow-y: auto;
          box-sizing: border-box;
          height: 100%;
        }

        /* HEADER */

        .header {
          display: flex;
          justify-content: space-between;
          border-bottom: 1px solid var(--divider-color);
          background-color: var(--card-background-color);
          position: absolute;
          top: 0;
          right: 0;
          left: 0;
          z-index: 3;
          padding: 16px;
        }
        .header_button {
          position: relative;
          right: -8px;
        }
        .header-content {
          display: flex;
          flex-wrap: wrap;
          flex-grow: 1;
          align-items: flex-start;
        }
        .header-content .img {
          height: 175px;
          width: 175px;
          margin-right: 16px;
          background-size: cover;
          border-radius: 2px;
          transition:
            width 0.4s,
            height 0.4s;
        }
        .header-info {
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          align-self: stretch;
          min-width: 0;
          flex: 1;
        }
        .header-info ha-button {
          display: block;
          padding-bottom: 16px;
        }
        .breadcrumb {
          display: flex;
          flex-direction: column;
          overflow: hidden;
          flex-grow: 1;
          padding-top: 16px;
        }
        .breadcrumb .title {
          font-size: var(--ha-font-size-4xl);
          line-height: var(--ha-line-height-condensed);
          font-weight: var(--ha-font-weight-bold);
          margin: 0;
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          padding-right: 8px;
        }
        .breadcrumb .previous-title {
          font-size: var(--ha-font-size-m);
          padding-bottom: 8px;
          color: var(--secondary-text-color);
          overflow: hidden;
          text-overflow: ellipsis;
          cursor: pointer;
          --mdc-icon-size: 14px;
        }
        .breadcrumb .subtitle {
          font-size: var(--ha-font-size-l);
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 0;
          transition:
            height 0.5s,
            margin 0.5s;
        }

        .not-shown {
          font-style: italic;
          color: var(--secondary-text-color);
          padding: 8px 16px 8px;
        }

        .grid.not-shown {
          display: flex;
          align-items: center;
          text-align: center;
        }

        /* ============= CHILDREN ============= */

        ha-list {
          --mdc-list-vertical-padding: 0;
          --mdc-list-item-graphic-margin: 0;
          --mdc-theme-text-icon-on-background: var(--secondary-text-color);
          margin-top: 10px;
        }

        ha-list li:last-child {
          display: none;
        }

        ha-list li[divider] {
          border-bottom-color: var(--divider-color);
        }

        ha-list-item {
          width: 100%;
        }

        div.children {
          display: grid;
          grid-template-columns: repeat(
            auto-fit,
            minmax(var(--media-browse-item-size, 175px), 0.1fr)
          );
          grid-gap: var(--ha-space-4);
          padding: 16px;
        }

        :host([dialog]) .children {
          grid-template-columns: repeat(
            auto-fit,
            minmax(var(--media-browse-item-size, 175px), 0.33fr)
          );
        }

        .child {
          display: flex;
          flex-direction: column;
          cursor: pointer;
        }

        ha-card {
          position: relative;
          width: 100%;
          box-sizing: border-box;
        }

        .children ha-card .thumbnail {
          width: 100%;
          position: relative;
          box-sizing: border-box;
          transition: padding-bottom 0.1s ease-out;
          padding-bottom: 100%;
        }

        .portrait ha-card .thumbnail {
          padding-bottom: 150%;
        }

        ha-card .image {
          border-radius: var(--ha-border-radius-sm) var(--ha-border-radius-sm)
            var(--ha-border-radius-square) var(--ha-border-radius-square);
        }

        .image {
          position: absolute;
          top: 0;
          right: 0;
          left: 0;
          bottom: 0;
          background-size: cover;
          background-repeat: no-repeat;
          background-position: center;
        }

        .centered-image {
          margin: 0 8px;
          background-size: contain;
        }

        .brand-image {
          background-size: 40%;
        }

        .children ha-card .icon-holder {
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .child .folder {
          color: var(--secondary-text-color);
          --mdc-icon-size: calc(var(--media-browse-item-size, 175px) * 0.4);
        }

        .child .icon {
          color: #00a9f7; /* Match the png color from brands repo */
          --mdc-icon-size: calc(var(--media-browse-item-size, 175px) * 0.4);
        }

        .child .play {
          position: absolute;
          transition: color 0.5s;
          border-radius: var(--ha-border-radius-circle);
          top: calc(50% - 40px);
          right: calc(50% - 35px);
          opacity: 0;
          transition: opacity 0.1s ease-out;
        }

        .child .play:not(.can_expand) {
          --mdc-icon-button-size: 70px;
          --mdc-icon-size: 48px;
          background-color: var(--primary-color);
          color: var(--text-primary-color);
        }

        ha-card:hover .image {
          filter: brightness(70%);
          transition: filter 0.5s;
        }

        ha-card:hover .play {
          opacity: 1;
        }

        ha-card:hover .play.can_expand {
          bottom: 8px;
        }

        .child .play.can_expand {
          background-color: rgba(var(--rgb-card-background-color), 0.5);
          top: auto;
          bottom: 0px;
          right: 8px;
          transition:
            bottom 0.1s ease-out,
            opacity 0.1s ease-out;
        }

        .child .title {
          font-size: var(--ha-font-size-l);
          padding-top: 16px;
          padding-left: 2px;
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          text-overflow: ellipsis;
        }

        .child ha-card .title {
          margin-bottom: 16px;
          padding-left: 16px;
        }

        ha-list-item .graphic {
          background-size: contain;
          background-repeat: no-repeat;
          background-position: center;
          border-radius: var(--ha-border-radius-sm);
          display: flex;
          align-content: center;
          align-items: center;
          line-height: initial;
        }

        ha-list-item .graphic .play {
          opacity: 0;
          transition: all 0.5s;
          background-color: rgba(var(--rgb-card-background-color), 0.5);
          border-radius: var(--ha-border-radius-circle);
          --mdc-icon-button-size: 40px;
        }

        ha-list-item:hover .graphic .play {
          opacity: 1;
          color: var(--primary-text-color);
        }

        ha-list-item .graphic .play.show {
          opacity: 1;
          background-color: transparent;
        }

        ha-list-item .title {
          margin-left: 16px;
          margin-inline-start: 16px;
          margin-inline-end: initial;
        }

        /* ============= Narrow ============= */

        :host([narrow]) {
          padding: 0;
        }

        :host([narrow]) .media-source {
          padding: 0 24px;
        }

        :host([narrow]) div.children {
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        }

        :host([narrow]) .breadcrumb .title {
          font-size: var(--ha-font-size-2xl);
        }
        :host([narrow]) .header {
          padding: 0;
        }
        :host([narrow]) .header.no-dialog {
          display: block;
        }
        :host([narrow]) .header_button {
          position: absolute;
          top: 14px;
          right: 8px;
        }
        :host([narrow]) .header-content {
          flex-direction: column;
          flex-wrap: nowrap;
        }
        :host([narrow]) .header-content .img {
          height: auto;
          width: 100%;
          margin-right: 0;
          padding-bottom: 50%;
          margin-bottom: 8px;
          position: relative;
          background-position: center;
          border-radius: var(--ha-border-radius-square);
          transition:
            width 0.4s,
            height 0.4s,
            padding-bottom 0.4s;
        }
        ha-fab {
          position: absolute;
          --mdc-theme-secondary: var(--primary-color);
          bottom: -20px;
          right: 20px;
        }
        :host([narrow]) .header-info ha-button {
          margin-top: 16px;
          margin-bottom: 8px;
        }
        :host([narrow]) .header-info {
          padding: 0 16px 8px;
        }

        /* ============= Scroll ============= */
        :host([scrolled]) .breadcrumb .subtitle {
          height: 0;
          margin: 0;
        }
        :host([scrolled]) .breadcrumb .title {
          -webkit-line-clamp: 1;
        }
        :host(:not([narrow])[scrolled]) .header:not(.no-img) ha-icon-button {
          align-self: center;
        }
        :host([scrolled]) .header-info ha-button,
        .no-img .header-info ha-button {
          padding-right: 4px;
        }
        :host([scrolled][narrow]) .no-img .header-info ha-button {
          padding-right: 16px;
        }
        :host([scrolled]) .header-info {
          flex-direction: row;
        }
        :host([scrolled]) .header-info ha-button {
          align-self: center;
          margin-top: 0;
          margin-bottom: 0;
          padding-bottom: 0;
        }
        :host([scrolled][narrow]) .no-img .header-info {
          flex-direction: row-reverse;
        }
        :host([scrolled][narrow]) .header-info {
          padding: 20px 24px 10px 24px;
          align-items: center;
        }
        :host([scrolled]) .header-content {
          align-items: flex-end;
          flex-direction: row;
        }
        :host([scrolled]) .header-content .img {
          height: 75px;
          width: 75px;
        }
        :host([scrolled]) .breadcrumb {
          padding-top: 0;
          align-self: center;
        }
        :host([scrolled][narrow]) .header-content .img {
          height: 100px;
          width: 100px;
          padding-bottom: initial;
          margin-bottom: 0;
        }
        :host([scrolled]) ha-fab {
          bottom: 0px;
          right: -24px;
          --mdc-fab-box-shadow: none;
          --mdc-theme-secondary: rgba(var(--rgb-primary-color), 0.5);
        }

        lit-virtualizer {
          height: 100%;
          overflow: overlay !important;
          contain: size layout !important;
        }

        lit-virtualizer.not_shown {
          height: calc(100% - 36px);
        }

        ha-browse-media-tts {
          direction: var(--direction);
        }
      `))]}}]);var i,p,m,g,q}(v.WF);(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"hass",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"entityId",void 0),(0,m.__decorate)([(0,g.MZ)()],ye.prototype,"action",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"preferredLayout",void 0),(0,m.__decorate)([(0,g.MZ)({type:Boolean})],ye.prototype,"dialog",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"navigateIds",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"accept",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"defaultId",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"defaultType",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"hideContentType",void 0),(0,m.__decorate)([(0,g.MZ)({attribute:!1})],ye.prototype,"contentIdHelper",void 0),(0,m.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],ye.prototype,"narrow",void 0),(0,m.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],ye.prototype,"scrolled",void 0),(0,m.__decorate)([(0,g.wk)()],ye.prototype,"_error",void 0),(0,m.__decorate)([(0,g.wk)()],ye.prototype,"_parentItem",void 0),(0,m.__decorate)([(0,g.wk)()],ye.prototype,"_currentItem",void 0),(0,m.__decorate)([(0,g.P)(".header")],ye.prototype,"_header",void 0),(0,m.__decorate)([(0,g.P)(".content")],ye.prototype,"_content",void 0),(0,m.__decorate)([(0,g.P)("lit-virtualizer")],ye.prototype,"_virtualizer",void 0),(0,m.__decorate)([(0,g.Ls)({passive:!0})],ye.prototype,"_scroll",null),ye=(0,m.__decorate)([(0,g.EM)("ha-media-player-browse")],ye),t()}catch(be){t(be)}}))},76019:function(e,t,i){i.d(t,{l:function(){return r}});i(23792),i(26099),i(3362),i(62953);var a=i(92542),r=(e,t)=>{(0,a.r)(e,"show-dialog",{dialogTag:"dialog-media-manage",dialogImport:()=>Promise.all([i.e("9035"),i.e("8638")]).then(i.bind(i,2909)),dialogParams:t})}},9923:function(e,t,i){i.d(t,{CY:function(){return s},Fn:function(){return o},Jz:function(){return c},VA:function(){return l},WI:function(){return h},iY:function(){return d},xw:function(){return n}});var a=i(61397),r=i(50264),o=(i(16280),(e,t)=>e.callWS({type:"media_source/browse_media",media_content_id:t})),n="__MANUAL_ENTRY__",s=e=>e.startsWith(n),c=e=>e.startsWith("media-source://media_source"),d=e=>e.startsWith("media-source://image_upload"),l=function(){var e=(0,r.A)((0,a.A)().m((function e(t,i,r){var o,n;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return(o=new FormData).append("media_content_id",i),o.append("file",r),e.n=1,t.fetchWithAuth("/api/media_source/local_source/upload",{method:"POST",body:o});case 1:if(413!==(n=e.v).status){e.n=2;break}throw new Error(`Uploaded file is too large (${r.name})`);case 2:if(200===n.status){e.n=3;break}throw new Error("Unknown error");case 3:return e.a(2,n.json())}}),e)})));return function(t,i,a){return e.apply(this,arguments)}}(),h=function(){var e=(0,r.A)((0,a.A)().m((function e(t,i){return(0,a.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.callWS({type:"media_source/local_source/remove",media_content_id:i}))}),e)})));return function(t,i){return e.apply(this,arguments)}}()},62001:function(e,t,i){i.d(t,{o:function(){return a}});i(74423);var a=(e,t)=>`https://${e.config.version.includes("b")?"rc":e.config.version.includes("dev")?"next":"www"}.home-assistant.io${t}`}}]);
//# sourceMappingURL=7683.7b13f4ebb58515ea.js.map