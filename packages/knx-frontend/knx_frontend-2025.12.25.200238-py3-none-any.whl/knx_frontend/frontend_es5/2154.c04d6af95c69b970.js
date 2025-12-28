"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2154"],{5841:function(e,t,a){var o,i,r=a(44734),n=a(56038),l=a(69683),s=a(6454),d=a(62826),h=a(96196),c=a(77845),p=e=>e,u=function(e){function t(){return(0,r.A)(this,t),(0,l.A)(this,t,arguments)}return(0,s.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,h.qy)(o||(o=p`
      <footer>
        <slot name="secondaryAction"></slot>
        <slot name="primaryAction"></slot>
      </footer>
    `))}}],[{key:"styles",get:function(){return[(0,h.AH)(i||(i=p`
        footer {
          display: flex;
          gap: var(--ha-space-3);
          justify-content: flex-end;
          align-items: center;
          width: 100%;
        }
      `))]}}])}(h.WF);u=(0,d.__decorate)([(0,c.EM)("ha-dialog-footer")],u)},86451:function(e,t,a){var o,i,r,n,l,s,d=a(44734),h=a(56038),c=a(69683),p=a(6454),u=(a(28706),a(62826)),g=a(96196),v=a(77845),f=e=>e,m=function(e){function t(){var e;(0,d.A)(this,t);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(e=(0,c.A)(this,t,[].concat(o))).subtitlePosition="below",e.showBorder=!1,e}return(0,p.A)(t,e),(0,h.A)(t,[{key:"render",value:function(){var e=(0,g.qy)(o||(o=f`<div class="header-title">
      <slot name="title"></slot>
    </div>`)),t=(0,g.qy)(i||(i=f`<div class="header-subtitle">
      <slot name="subtitle"></slot>
    </div>`));return(0,g.qy)(r||(r=f`
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
    `),"above"===this.subtitlePosition?(0,g.qy)(n||(n=f`${0}${0}`),t,e):(0,g.qy)(l||(l=f`${0}${0}`),e,t))}}],[{key:"styles",get:function(){return[(0,g.AH)(s||(s=f`
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
      `))]}}])}(g.WF);(0,u.__decorate)([(0,v.MZ)({type:String,attribute:"subtitle-position"})],m.prototype,"subtitlePosition",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],m.prototype,"showBorder",void 0),m=(0,u.__decorate)([(0,v.EM)("ha-dialog-header")],m)},36626:function(e,t,a){a.a(e,(async function(e,t){try{var o=a(61397),i=a(50264),r=a(44734),n=a(56038),l=a(75864),s=a(69683),d=a(6454),h=a(25460),c=(a(28706),a(62826)),p=a(93900),u=a(96196),g=a(77845),v=a(32288),f=a(92542),m=a(39396),w=(a(86451),a(60733),e([p]));p=(w.then?(await w)():w)[0];var y,b,_,x,k,A,$=e=>e,C=function(e){function t(){var e;(0,r.A)(this,t);for(var a=arguments.length,n=new Array(a),d=0;d<a;d++)n[d]=arguments[d];return(e=(0,s.A)(this,t,[].concat(n))).open=!1,e.type="standard",e.width="medium",e.preventScrimClose=!1,e.headerSubtitlePosition="below",e.flexContent=!1,e._open=!1,e._bodyScrolled=!1,e._handleShow=(0,i.A)((0,o.A)().m((function t(){return(0,o.A)().w((function(t){for(;;)switch(t.n){case 0:return e._open=!0,(0,f.r)((0,l.A)(e),"opened"),t.n=1,e.updateComplete;case 1:requestAnimationFrame((()=>{var t;null===(t=e.querySelector("[autofocus]"))||void 0===t||t.focus()}));case 2:return t.a(2)}}),t)}))),e._handleAfterShow=()=>{(0,f.r)((0,l.A)(e),"after-show")},e._handleAfterHide=()=>{e._open=!1,(0,f.r)((0,l.A)(e),"closed")},e}return(0,d.A)(t,e),(0,n.A)(t,[{key:"updated",value:function(e){(0,h.A)(t,"updated",this,3)([e]),e.has("open")&&(this._open=this.open)}},{key:"render",value:function(){var e,t;return(0,u.qy)(y||(y=$`
      <wa-dialog
        .open=${0}
        .lightDismiss=${0}
        without-header
        aria-labelledby=${0}
        aria-describedby=${0}
        @wa-show=${0}
        @wa-after-show=${0}
        @wa-after-hide=${0}
      >
        <slot name="header">
          <ha-dialog-header
            .subtitlePosition=${0}
            .showBorder=${0}
          >
            <slot name="headerNavigationIcon" slot="navigationIcon">
              <ha-icon-button
                data-dialog="close"
                .label=${0}
                .path=${0}
              ></ha-icon-button>
            </slot>
            ${0}
            ${0}
            <slot name="headerActionItems" slot="actionItems"></slot>
          </ha-dialog-header>
        </slot>
        <div class="body ha-scrollbar" @scroll=${0}>
          <slot></slot>
        </div>
        <slot name="footer" slot="footer"></slot>
      </wa-dialog>
    `),this._open,!this.preventScrimClose,(0,v.J)(this.ariaLabelledBy||(void 0!==this.headerTitle?"ha-wa-dialog-title":void 0)),(0,v.J)(this.ariaDescribedBy),this._handleShow,this._handleAfterShow,this._handleAfterHide,this.headerSubtitlePosition,this._bodyScrolled,null!==(e=null===(t=this.hass)||void 0===t?void 0:t.localize("ui.common.close"))&&void 0!==e?e:"Close","M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",void 0!==this.headerTitle?(0,u.qy)(b||(b=$`<span slot="title" class="title" id="ha-wa-dialog-title">
                  ${0}
                </span>`),this.headerTitle):(0,u.qy)(_||(_=$`<slot name="headerTitle" slot="title"></slot>`)),void 0!==this.headerSubtitle?(0,u.qy)(x||(x=$`<span slot="subtitle">${0}</span>`),this.headerSubtitle):(0,u.qy)(k||(k=$`<slot name="headerSubtitle" slot="subtitle"></slot>`)),this._handleBodyScroll)}},{key:"disconnectedCallback",value:function(){(0,h.A)(t,"disconnectedCallback",this,3)([]),this._open=!1}},{key:"_handleBodyScroll",value:function(e){this._bodyScrolled=e.target.scrollTop>0}}])}(u.WF);C.styles=[m.dp,(0,u.AH)(A||(A=$`
      wa-dialog {
        --full-width: var(--ha-dialog-width-full, min(95vw, var(--safe-width)));
        --width: min(var(--ha-dialog-width-md, 580px), var(--full-width));
        --spacing: var(--dialog-content-padding, var(--ha-space-6));
        --show-duration: var(--ha-dialog-show-duration, 200ms);
        --hide-duration: var(--ha-dialog-hide-duration, 200ms);
        --ha-dialog-surface-background: var(
          --card-background-color,
          var(--ha-color-surface-default)
        );
        --wa-color-surface-raised: var(
          --ha-dialog-surface-background,
          var(--card-background-color, var(--ha-color-surface-default))
        );
        --wa-panel-border-radius: var(
          --ha-dialog-border-radius,
          var(--ha-border-radius-3xl)
        );
        max-width: var(--ha-dialog-max-width, var(--safe-width));
      }

      :host([width="small"]) wa-dialog {
        --width: min(var(--ha-dialog-width-sm, 320px), var(--full-width));
      }

      :host([width="large"]) wa-dialog {
        --width: min(var(--ha-dialog-width-lg, 1024px), var(--full-width));
      }

      :host([width="full"]) wa-dialog {
        --width: var(--full-width);
      }

      wa-dialog::part(dialog) {
        min-width: var(--width, var(--full-width));
        max-width: var(--width, var(--full-width));
        max-height: var(
          --ha-dialog-max-height,
          calc(var(--safe-height) - var(--ha-space-20))
        );
        min-height: var(--ha-dialog-min-height);
        margin-top: var(--dialog-surface-margin-top, auto);
        /* Used to offset the dialog from the safe areas when space is limited */
        transform: translate(
          calc(
            var(--safe-area-offset-left, var(--ha-space-0)) - var(
                --safe-area-offset-right,
                var(--ha-space-0)
              )
          ),
          calc(
            var(--safe-area-offset-top, var(--ha-space-0)) - var(
                --safe-area-offset-bottom,
                var(--ha-space-0)
              )
          )
        );
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      @media all and (max-width: 450px), all and (max-height: 500px) {
        :host([type="standard"]) {
          --ha-dialog-border-radius: var(--ha-space-0);

          wa-dialog {
            /* Make the container fill the whole screen width and not the safe width */
            --full-width: var(--ha-dialog-width-full, 100vw);
            --width: var(--full-width);
          }

          wa-dialog::part(dialog) {
            /* Make the dialog fill the whole screen height and not the safe height */
            min-height: var(--ha-dialog-min-height, 100vh);
            min-height: var(--ha-dialog-min-height, 100dvh);
            max-height: var(--ha-dialog-max-height, 100vh);
            max-height: var(--ha-dialog-max-height, 100dvh);
            margin-top: 0;
            margin-bottom: 0;
            /* Use safe area as padding instead of the container size */
            padding-top: var(--safe-area-inset-top);
            padding-bottom: var(--safe-area-inset-bottom);
            padding-left: var(--safe-area-inset-left);
            padding-right: var(--safe-area-inset-right);
            /* Reset the transform to center the dialog */
            transform: none;
          }
        }
      }

      .header-title-container {
        display: flex;
        align-items: center;
      }

      .header-title {
        margin: 0;
        margin-bottom: 0;
        color: var(--ha-dialog-header-title-color, var(--primary-text-color));
        font-size: var(
          --ha-dialog-header-title-font-size,
          var(--ha-font-size-2xl)
        );
        line-height: var(
          --ha-dialog-header-title-line-height,
          var(--ha-line-height-condensed)
        );
        font-weight: var(
          --ha-dialog-header-title-font-weight,
          var(--ha-font-weight-normal)
        );
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-right: var(--ha-space-3);
      }

      wa-dialog::part(body) {
        padding: 0;
        display: flex;
        flex-direction: column;
        max-width: 100%;
        overflow: hidden;
      }

      .body {
        position: var(--dialog-content-position, relative);
        padding: 0 var(--dialog-content-padding, var(--ha-space-6))
          var(--dialog-content-padding, var(--ha-space-6))
          var(--dialog-content-padding, var(--ha-space-6));
        overflow: auto;
        flex-grow: 1;
      }
      :host([flexcontent]) .body {
        max-width: 100%;
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      wa-dialog::part(footer) {
        padding: var(--ha-space-0);
      }

      ::slotted([slot="footer"]) {
        display: flex;
        padding: var(--ha-space-3) var(--ha-space-4) var(--ha-space-4)
          var(--ha-space-4);
        gap: var(--ha-space-3);
        justify-content: flex-end;
        align-items: center;
        width: 100%;
      }
    `))],(0,c.__decorate)([(0,g.MZ)({attribute:!1})],C.prototype,"hass",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"aria-labelledby"})],C.prototype,"ariaLabelledBy",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"aria-describedby"})],C.prototype,"ariaDescribedBy",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],C.prototype,"open",void 0),(0,c.__decorate)([(0,g.MZ)({reflect:!0})],C.prototype,"type",void 0),(0,c.__decorate)([(0,g.MZ)({type:String,reflect:!0,attribute:"width"})],C.prototype,"width",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0,attribute:"prevent-scrim-close"})],C.prototype,"preventScrimClose",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"header-title"})],C.prototype,"headerTitle",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"header-subtitle"})],C.prototype,"headerSubtitle",void 0),(0,c.__decorate)([(0,g.MZ)({type:String,attribute:"header-subtitle-position"})],C.prototype,"headerSubtitlePosition",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0,attribute:"flexcontent"})],C.prototype,"flexContent",void 0),(0,c.__decorate)([(0,g.wk)()],C.prototype,"_open",void 0),(0,c.__decorate)([(0,g.P)(".body")],C.prototype,"bodyContainer",void 0),(0,c.__decorate)([(0,g.wk)()],C.prototype,"_bodyScrolled",void 0),(0,c.__decorate)([(0,g.Ls)({passive:!0})],C.prototype,"_handleBodyScroll",null),C=(0,c.__decorate)([(0,g.EM)("ha-wa-dialog")],C),t()}catch(L){t(L)}}))},17262:function(e,t,a){var o,i,r,n=a(61397),l=a(50264),s=a(44734),d=a(56038),h=a(69683),c=a(6454),p=(a(28706),a(2008),a(18111),a(22489),a(26099),a(62826)),u=a(96196),g=a(77845),v=(a(60733),a(60961),a(78740),a(92542)),f=e=>e,m=function(e){function t(){var e;(0,s.A)(this,t);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(e=(0,h.A)(this,t,[].concat(o))).suffix=!1,e.autofocus=!1,e}return(0,c.A)(t,e),(0,d.A)(t,[{key:"focus",value:function(){var e;null===(e=this._input)||void 0===e||e.focus()}},{key:"render",value:function(){return(0,u.qy)(o||(o=f`
      <ha-textfield
        .autofocus=${0}
        autocomplete="off"
        .label=${0}
        .value=${0}
        icon
        .iconTrailing=${0}
        @input=${0}
      >
        <slot name="prefix" slot="leadingIcon">
          <ha-svg-icon
            tabindex="-1"
            class="prefix"
            .path=${0}
          ></ha-svg-icon>
        </slot>
        <div class="trailing" slot="trailingIcon">
          ${0}
          <slot name="suffix"></slot>
        </div>
      </ha-textfield>
    `),this.autofocus,this.label||this.hass.localize("ui.common.search"),this.filter||"",this.filter||this.suffix,this._filterInputChanged,"M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z",this.filter&&(0,u.qy)(i||(i=f`
            <ha-icon-button
              @click=${0}
              .label=${0}
              .path=${0}
              class="clear-button"
            ></ha-icon-button>
          `),this._clearSearch,this.hass.localize("ui.common.clear"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"))}},{key:"_filterChanged",value:(p=(0,l.A)((0,n.A)().m((function e(t){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:(0,v.r)(this,"value-changed",{value:String(t)});case 1:return e.a(2)}}),e,this)}))),function(e){return p.apply(this,arguments)})},{key:"_filterInputChanged",value:(r=(0,l.A)((0,n.A)().m((function e(t){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:this._filterChanged(t.target.value);case 1:return e.a(2)}}),e,this)}))),function(e){return r.apply(this,arguments)})},{key:"_clearSearch",value:(a=(0,l.A)((0,n.A)().m((function e(){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:this._filterChanged("");case 1:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})}]);var a,r,p}(u.WF);m.styles=(0,u.AH)(r||(r=f`
    :host {
      display: inline-flex;
    }
    ha-svg-icon,
    ha-icon-button {
      color: var(--primary-text-color);
    }
    ha-svg-icon {
      outline: none;
    }
    .clear-button {
      --mdc-icon-size: 20px;
    }
    ha-textfield {
      display: inherit;
    }
    .trailing {
      display: flex;
      align-items: center;
    }
  `)),(0,p.__decorate)([(0,g.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,p.__decorate)([(0,g.MZ)()],m.prototype,"filter",void 0),(0,p.__decorate)([(0,g.MZ)({type:Boolean})],m.prototype,"suffix",void 0),(0,p.__decorate)([(0,g.MZ)({type:Boolean})],m.prototype,"autofocus",void 0),(0,p.__decorate)([(0,g.MZ)({type:String})],m.prototype,"label",void 0),(0,p.__decorate)([(0,g.P)("ha-textfield",!0)],m.prototype,"_input",void 0),m=(0,p.__decorate)([(0,g.EM)("search-input")],m)},193:function(e,t,a){a.a(e,(async function(e,o){try{a.r(t),a.d(t,{KnxGaSelectDialog:function(){return S}});var i=a(61397),r=a(50264),n=a(78261),l=a(44734),s=a(56038),d=a(69683),h=a(6454),c=(a(28706),a(2008),a(74423),a(62062),a(44114),a(26910),a(18111),a(22489),a(7588),a(61701),a(5506),a(26099),a(42762),a(23500),a(62826)),p=a(22786),u=a(96196),g=a(77845),v=a(94333),f=a(36626),m=a(89473),w=(a(5841),a(17262),a(42921),a(23897),a(92542)),y=a(39396),b=e([f,m]);[f,m]=b.then?(await b)():b;var _,x,k,A,$,C,L,M=e=>e,S=function(e){function t(){var e;(0,l.A)(this,t);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(e=(0,d.A)(this,t,[].concat(o)))._open=!1,e._groupAddresses=[],e._filter="",e._groupItems=(0,p.A)(((e,t,a)=>{var o=e.trim().toLowerCase();if(!a||!a.group_ranges)return[];var i=t.filter((e=>{var t,a;if(!o)return!0;var i=null!==(t=e.address)&&void 0!==t?t:"",r=null!==(a=e.name)&&void 0!==a?a:"";return i.toLowerCase().includes(o)||r.toLowerCase().includes(o)})),r=function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0,a=[];return Object.entries(e).forEach((e=>{var o,l=(0,n.A)(e,2),s=l[0],d=l[1],h=null!==(o=d.group_addresses)&&void 0!==o?o:[],c=i.filter((e=>h.includes(e.address))),p=d.group_ranges?r(d.group_ranges,t+1):[];(c.length>0||p.length>0)&&a.push({title:`${s} ${d.name}`.trim(),items:c.sort(((e,t)=>e.raw_address-t.raw_address)),depth:t,childGroups:p})})),a};return r(a.group_ranges)})),e}return(0,h.A)(t,e),(0,s.A)(t,[{key:"showDialog",value:(a=(0,r.A)((0,i.A)().m((function e(t){var a,o;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:this._params=t,this._groupAddresses=null!==(a=t.groupAddresses)&&void 0!==a?a:[],this.knx=t.knx,this._selected=null!==(o=t.initialSelection)&&void 0!==o?o:this._selected,this._open=!0;case 1:return e.a(2)}}),e,this)}))),function(e){return a.apply(this,arguments)})},{key:"closeDialog",value:function(e){return this._dialogClosed(),!0}},{key:"_cancel",value:function(){var e;this._selected=void 0,null!==(e=this._params)&&void 0!==e&&e.onClose&&this._params.onClose(void 0),this._dialogClosed()}},{key:"_confirm",value:function(){var e;null!==(e=this._params)&&void 0!==e&&e.onClose&&this._params.onClose(this._selected),this._dialogClosed()}},{key:"_itemKeydown",value:function(e){if("Enter"===e.key){e.preventDefault();var t=e.currentTarget.getAttribute("value");t&&(this._selected=t,this._confirm())}}},{key:"_onDoubleClick",value:function(e){var t=e.currentTarget.getAttribute("value");this._selected=null!=t?t:void 0,this._selected&&this._confirm()}},{key:"_onSelect",value:function(e){var t=e.currentTarget.getAttribute("value");this._selected=null!=t?t:void 0}},{key:"_onFilterChanged",value:function(e){var t,a;this._filter=null!==(t=null===(a=e.detail)||void 0===a?void 0:a.value)&&void 0!==t?t:""}},{key:"_dialogClosed",value:function(){this._open=!1,this._params=void 0,this._filter="",this._selected=void 0,(0,w.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"_renderGroup",value:function(e){return(0,u.qy)(_||(_=M`
      <div class="group-section">
        <div class="group-title" style="--group-depth: ${0}">${0}</div>
        ${0}
        ${0}
      </div>
    `),e.depth,e.title,e.items.length>0?(0,u.qy)(x||(x=M`<ha-md-list>
              ${0}
            </ha-md-list>`),e.items.map((e=>{var t,a=this._selected===e.address;return(0,u.qy)(k||(k=M`<ha-md-list-item
                  interactive
                  type="button"
                  value=${0}
                  @click=${0}
                  @dblclick=${0}
                  @keydown=${0}
                >
                  <div class=${0} slot="headline">
                    <div class="ga-address">${0}</div>
                    <div class="ga-name">${0}</div>
                  </div>
                </ha-md-list-item>`),e.address,this._onSelect,this._onDoubleClick,this._itemKeydown,(0,v.H)({"ga-row":!0,selected:a}),e.address,null!==(t=e.name)&&void 0!==t?t:"")}))):u.s6,e.childGroups.map((e=>this._renderGroup(e))))}},{key:"render",value:function(){var e,t,a;if(!this._params||!this.hass)return u.s6;var o=!(null!==(e=this.knx.projectData)&&void 0!==e&&e.group_ranges),i=(null===(t=this._groupAddresses)||void 0===t?void 0:t.length)>0,r=i?this._groupItems(this._filter,this._groupAddresses,this.knx.projectData):[],n=r.length>0;return(0,u.qy)(A||(A=M`<ha-wa-dialog
      .hass=${0}
      .open=${0}
      width=${0}
      .headerTitle=${0}
      @closed=${0}
    >
      <div class="dialog-body">
        <search-input
          ?autofocus=${0}
          .hass=${0}
          .filter=${0}
          @value-changed=${0}
          .label=${0}
        ></search-input>

        <div class="ga-list-container">
          ${0}
        </div>
      </div>

      <ha-dialog-footer slot="footer">
        <ha-button slot="secondaryAction" appearance="plain" @click=${0}>
          ${0}
        </ha-button>
        <ha-button slot="primaryAction" @click=${0} .disabled=${0}>
          ${0}
        </ha-button>
      </ha-dialog-footer>
    </ha-wa-dialog>`),this.hass,this._open,null!==(a=this._params.width)&&void 0!==a?a:"medium",this._params.title,this._dialogClosed,!0,this.hass,this._filter,this._onFilterChanged,this.hass.localize("ui.common.search"),o||!i?(0,u.qy)($||($=M`<div class="empty-state">
                ${0}
              </div>`),this.hass.localize("component.knx.config_panel.entities.create._.knx.knx_group_address.group_address_none_for_dpt")):n?r.map((e=>this._renderGroup(e))):(0,u.qy)(C||(C=M`<div class="empty-state">
                  ${0}
                </div>`),this.hass.localize("component.knx.config_panel.entities.create._.knx.knx_group_address.group_address_none_for_filter")),this._cancel,this.hass.localize("ui.common.cancel"),this._confirm,!this._selected,this.hass.localize("ui.common.ok"))}}],[{key:"styles",get:function(){return[y.nA,(0,u.AH)(L||(L=M`
        @media all and (min-width: 600px) {
          ha-wa-dialog {
            --mdc-dialog-min-width: 360px;
          }
        }

        .dialog-body {
          display: flex;
          flex-direction: column;
          gap: var(--ha-space-2, 8px);
          height: 100%;
          min-height: 0;
        }

        search-input {
          display: block;
          width: 100%;
        }

        ha-md-list {
          padding: 0;
        }

        .ga-list-container {
          flex: 1 1 auto;
          min-height: 0;
          overflow: auto;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          padding: 0;
        }

        .group-title {
          position: sticky;
          top: calc(var(--group-title-height, 40px) * min(1, var(--group-depth, 0)));
          z-index: calc(10 - var(--group-depth, 0));
          height: var(--group-title-height, 40px);
          box-sizing: border-box;
          display: flex;
          align-items: center;
          font-weight: 600;
          padding: 6px 8px;
          padding-left: calc(8px + var(--group-depth, 0) * 8px);
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          border-bottom: 1px solid var(--divider-color);
        }

        .empty-state {
          padding: 12px;
          color: var(--secondary-text-color);
          font-style: italic;
        }

        .ga-row {
          display: grid;
          grid-template-columns: 10ch minmax(0, 1fr);
          align-items: center;
          gap: var(--ha-space-2, 8px);
          padding: 6px 8px;
          border-radius: 4px;
        }

        .ga-row.selected {
          background-color: rgba(var(--rgb-primary-color), 0.08);
          outline: 2px solid rgba(var(--rgb-accent-color), 0.12);
        }

        .ga-address {
          font-family:
            ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace;
          width: 100%;
          color: var(--secondary-text-color);
          white-space: nowrap;
        }

        .ga-name {
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          min-width: 0;
        }
      `))]}}]);var a}(u.WF);(0,c.__decorate)([(0,g.MZ)({attribute:!1})],S.prototype,"hass",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:!1})],S.prototype,"knx",void 0),(0,c.__decorate)([(0,g.wk)()],S.prototype,"_open",void 0),(0,c.__decorate)([(0,g.wk)()],S.prototype,"_params",void 0),(0,c.__decorate)([(0,g.wk)()],S.prototype,"_groupAddresses",void 0),(0,c.__decorate)([(0,g.wk)()],S.prototype,"_selected",void 0),(0,c.__decorate)([(0,g.wk)()],S.prototype,"_filter",void 0),S=(0,c.__decorate)([(0,g.EM)("knx-ga-select-dialog")],S),o()}catch(q){o(q)}}))},99793:function(e,t,a){var o,i=a(96196);t.A=(0,i.AH)(o||(o=(e=>e)`:host {
  --width: 31rem;
  --spacing: var(--wa-space-l);
  --show-duration: 200ms;
  --hide-duration: 200ms;
  display: none;
}
:host([open]) {
  display: block;
}
.dialog {
  display: flex;
  flex-direction: column;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  width: var(--width);
  max-width: calc(100% - var(--wa-space-2xl));
  max-height: calc(100% - var(--wa-space-2xl));
  background-color: var(--wa-color-surface-raised);
  border-radius: var(--wa-panel-border-radius);
  border: none;
  box-shadow: var(--wa-shadow-l);
  padding: 0;
  margin: auto;
}
.dialog.show {
  animation: show-dialog var(--show-duration) ease;
}
.dialog.show::backdrop {
  animation: show-backdrop var(--show-duration, 200ms) ease;
}
.dialog.hide {
  animation: show-dialog var(--hide-duration) ease reverse;
}
.dialog.hide::backdrop {
  animation: show-backdrop var(--hide-duration, 200ms) ease reverse;
}
.dialog.pulse {
  animation: pulse 250ms ease;
}
.dialog:focus {
  outline: none;
}
@media screen and (max-width: 420px) {
  .dialog {
    max-height: 80vh;
  }
}
.open {
  display: flex;
  opacity: 1;
}
.header {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: nowrap;
  padding-inline-start: var(--spacing);
  padding-block-end: 0;
  padding-inline-end: calc(var(--spacing) - var(--wa-form-control-padding-block));
  padding-block-start: calc(var(--spacing) - var(--wa-form-control-padding-block));
}
.title {
  align-self: center;
  flex: 1 1 auto;
  font-family: inherit;
  font-size: var(--wa-font-size-l);
  font-weight: var(--wa-font-weight-heading);
  line-height: var(--wa-line-height-condensed);
  margin: 0;
}
.header-actions {
  align-self: start;
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: end;
  gap: var(--wa-space-2xs);
  padding-inline-start: var(--spacing);
}
.header-actions wa-button,
.header-actions ::slotted(wa-button) {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}
.body {
  flex: 1 1 auto;
  display: block;
  padding: var(--spacing);
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}
.body:focus {
  outline: none;
}
.body:focus-visible {
  outline: var(--wa-focus-ring);
  outline-offset: var(--wa-focus-ring-offset);
}
.footer {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--wa-space-xs);
  justify-content: end;
  padding: var(--spacing);
  padding-block-start: 0;
}
.footer ::slotted(wa-button:not(:first-of-type)) {
  margin-inline-start: var(--wa-spacing-xs);
}
.dialog::backdrop {
  background-color: var(--wa-color-overlay-modal, rgb(0 0 0 / 0.25));
}
@keyframes pulse {
  0% {
    scale: 1;
  }
  50% {
    scale: 1.02;
  }
  100% {
    scale: 1;
  }
}
@keyframes show-dialog {
  from {
    opacity: 0;
    scale: 0.8;
  }
  to {
    opacity: 1;
    scale: 1;
  }
}
@keyframes show-backdrop {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (forced-colors: active) {
  .dialog {
    border: solid 1px white;
  }
}
`))},93900:function(e,t,a){a.a(e,(async function(e,t){try{var o=a(78261),i=a(61397),r=a(50264),n=a(44734),l=a(56038),s=a(69683),d=a(6454),h=a(25460),c=(a(27495),a(90906),a(96196)),p=a(77845),u=a(94333),g=a(32288),v=a(17051),f=a(42462),m=a(28438),w=a(98779),y=a(27259),b=a(31247),_=a(97039),x=a(92070),k=a(9395),A=a(32510),$=a(17060),C=a(88496),L=a(99793),M=e([C,$]);[C,$]=M.then?(await M)():M;var S,q,D,Z=e=>e,z=Object.defineProperty,B=Object.getOwnPropertyDescriptor,E=(e,t,a,o)=>{for(var i,r=o>1?void 0:o?B(t,a):t,n=e.length-1;n>=0;n--)(i=e[n])&&(r=(o?i(t,a,r):i(r))||r);return o&&r&&z(t,a,r),r},P=function(e){function t(){var e;return(0,n.A)(this,t),(e=(0,s.A)(this,t,arguments)).localize=new $.c(e),e.hasSlotController=new x.X(e,"footer","header-actions","label"),e.open=!1,e.label="",e.withoutHeader=!1,e.lightDismiss=!1,e.handleDocumentKeyDown=t=>{"Escape"===t.key&&e.open&&(t.preventDefault(),t.stopPropagation(),e.requestClose(e.dialog))},e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"firstUpdated",value:function(){this.open&&(this.addOpenListeners(),this.dialog.showModal(),(0,_.JG)(this))}},{key:"disconnectedCallback",value:function(){(0,h.A)(t,"disconnectedCallback",this,3)([]),(0,_.I7)(this),this.removeOpenListeners()}},{key:"requestClose",value:(p=(0,r.A)((0,i.A)().m((function e(t){var a,o;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:if(a=new m.L({source:t}),this.dispatchEvent(a),!a.defaultPrevented){e.n=1;break}return this.open=!0,(0,y.Ud)(this.dialog,"pulse"),e.a(2);case 1:return this.removeOpenListeners(),e.n=2,(0,y.Ud)(this.dialog,"hide");case 2:this.open=!1,this.dialog.close(),(0,_.I7)(this),"function"==typeof(null==(o=this.originalTrigger)?void 0:o.focus)&&setTimeout((()=>o.focus())),this.dispatchEvent(new v.Z);case 3:return e.a(2)}}),e,this)}))),function(e){return p.apply(this,arguments)})},{key:"addOpenListeners",value:function(){document.addEventListener("keydown",this.handleDocumentKeyDown)}},{key:"removeOpenListeners",value:function(){document.removeEventListener("keydown",this.handleDocumentKeyDown)}},{key:"handleDialogCancel",value:function(e){e.preventDefault(),this.dialog.classList.contains("hide")||e.target!==this.dialog||this.requestClose(this.dialog)}},{key:"handleDialogClick",value:function(e){var t=e.target.closest('[data-dialog="close"]');t&&(e.stopPropagation(),this.requestClose(t))}},{key:"handleDialogPointerDown",value:(o=(0,r.A)((0,i.A)().m((function e(t){return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:if(t.target!==this.dialog){e.n=2;break}if(!this.lightDismiss){e.n=1;break}this.requestClose(this.dialog),e.n=2;break;case 1:return e.n=2,(0,y.Ud)(this.dialog,"pulse");case 2:return e.a(2)}}),e,this)}))),function(e){return o.apply(this,arguments)})},{key:"handleOpenChange",value:function(){this.open&&!this.dialog.open?this.show():!this.open&&this.dialog.open&&(this.open=!0,this.requestClose(this.dialog))}},{key:"show",value:(a=(0,r.A)((0,i.A)().m((function e(){var t;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:if(t=new w.k,this.dispatchEvent(t),!t.defaultPrevented){e.n=1;break}return this.open=!1,e.a(2);case 1:return this.addOpenListeners(),this.originalTrigger=document.activeElement,this.open=!0,this.dialog.showModal(),(0,_.JG)(this),requestAnimationFrame((()=>{var e=this.querySelector("[autofocus]");e&&"function"==typeof e.focus?e.focus():this.dialog.focus()})),e.n=2,(0,y.Ud)(this.dialog,"show");case 2:this.dispatchEvent(new f.q);case 3:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"render",value:function(){var e,t=!this.withoutHeader,a=this.hasSlotController.test("footer");return(0,c.qy)(S||(S=Z`
      <dialog
        aria-labelledby=${0}
        aria-describedby=${0}
        part="dialog"
        class=${0}
        @cancel=${0}
        @click=${0}
        @pointerdown=${0}
      >
        ${0}

        <div part="body" class="body"><slot></slot></div>

        ${0}
      </dialog>
    `),null!==(e=this.ariaLabelledby)&&void 0!==e?e:"title",(0,g.J)(this.ariaDescribedby),(0,u.H)({dialog:!0,open:this.open}),this.handleDialogCancel,this.handleDialogClick,this.handleDialogPointerDown,t?(0,c.qy)(q||(q=Z`
              <header part="header" class="header">
                <h2 part="title" class="title" id="title">
                  <!-- If there's no label, use an invisible character to prevent the header from collapsing -->
                  <slot name="label"> ${0} </slot>
                </h2>
                <div part="header-actions" class="header-actions">
                  <slot name="header-actions"></slot>
                  <wa-button
                    part="close-button"
                    exportparts="base:close-button__base"
                    class="close"
                    appearance="plain"
                    @click="${0}"
                  >
                    <wa-icon
                      name="xmark"
                      label=${0}
                      library="system"
                      variant="solid"
                    ></wa-icon>
                  </wa-button>
                </div>
              </header>
            `),this.label.length>0?this.label:String.fromCharCode(8203),(e=>this.requestClose(e.target)),this.localize.term("close")):"",a?(0,c.qy)(D||(D=Z`
              <footer part="footer" class="footer">
                <slot name="footer"></slot>
              </footer>
            `)):"")}}]);var a,o,p}(A.A);P.css=L.A,E([(0,p.P)(".dialog")],P.prototype,"dialog",2),E([(0,p.MZ)({type:Boolean,reflect:!0})],P.prototype,"open",2),E([(0,p.MZ)({reflect:!0})],P.prototype,"label",2),E([(0,p.MZ)({attribute:"without-header",type:Boolean,reflect:!0})],P.prototype,"withoutHeader",2),E([(0,p.MZ)({attribute:"light-dismiss",type:Boolean})],P.prototype,"lightDismiss",2),E([(0,p.MZ)({attribute:"aria-labelledby"})],P.prototype,"ariaLabelledby",2),E([(0,p.MZ)({attribute:"aria-describedby"})],P.prototype,"ariaDescribedby",2),E([(0,k.w)("open",{waitUntilFirstUpdate:!0})],P.prototype,"handleOpenChange",1),P=E([(0,p.EM)("wa-dialog")],P),document.addEventListener("click",(e=>{var t=e.target.closest("[data-dialog]");if(t instanceof Element){var a=(0,b.v)(t.getAttribute("data-dialog")||""),i=(0,o.A)(a,2),r=i[0],n=i[1];if("open"===r&&null!=n&&n.length){var l=t.getRootNode().getElementById(n);"wa-dialog"===(null==l?void 0:l.localName)?l.open=!0:console.warn(`A dialog with an ID of "${n}" could not be found in this document.`)}}})),c.S$||document.addEventListener("pointerdown",(()=>{})),t()}catch(I){t(I)}}))}}]);
//# sourceMappingURL=2154.c04d6af95c69b970.js.map