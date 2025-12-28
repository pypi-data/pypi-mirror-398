"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7911"],{86451:function(e,a,t){var i,o,r,n,l,s,d=t(44734),h=t(56038),c=t(69683),p=t(6454),u=(t(28706),t(62826)),g=t(96196),v=t(77845),f=e=>e,w=function(e){function a(){var e;(0,d.A)(this,a);for(var t=arguments.length,i=new Array(t),o=0;o<t;o++)i[o]=arguments[o];return(e=(0,c.A)(this,a,[].concat(i))).subtitlePosition="below",e.showBorder=!1,e}return(0,p.A)(a,e),(0,h.A)(a,[{key:"render",value:function(){var e=(0,g.qy)(i||(i=f`<div class="header-title">
      <slot name="title"></slot>
    </div>`)),a=(0,g.qy)(o||(o=f`<div class="header-subtitle">
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
    `),"above"===this.subtitlePosition?(0,g.qy)(n||(n=f`${0}${0}`),a,e):(0,g.qy)(l||(l=f`${0}${0}`),e,a))}}],[{key:"styles",get:function(){return[(0,g.AH)(s||(s=f`
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
      `))]}}])}(g.WF);(0,u.__decorate)([(0,v.MZ)({type:String,attribute:"subtitle-position"})],w.prototype,"subtitlePosition",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],w.prototype,"showBorder",void 0),w=(0,u.__decorate)([(0,v.EM)("ha-dialog-header")],w)},36626:function(e,a,t){t.a(e,(async function(e,a){try{var i=t(61397),o=t(50264),r=t(44734),n=t(56038),l=t(75864),s=t(69683),d=t(6454),h=t(25460),c=(t(28706),t(62826)),p=t(93900),u=t(96196),g=t(77845),v=t(32288),f=t(92542),w=t(39396),m=(t(86451),t(60733),e([p]));p=(m.then?(await m)():m)[0];var y,b,x,_,k,A,$=e=>e,C=function(e){function a(){var e;(0,r.A)(this,a);for(var t=arguments.length,n=new Array(t),d=0;d<t;d++)n[d]=arguments[d];return(e=(0,s.A)(this,a,[].concat(n))).open=!1,e.type="standard",e.width="medium",e.preventScrimClose=!1,e.headerSubtitlePosition="below",e.flexContent=!1,e._open=!1,e._bodyScrolled=!1,e._handleShow=(0,o.A)((0,i.A)().m((function a(){return(0,i.A)().w((function(a){for(;;)switch(a.n){case 0:return e._open=!0,(0,f.r)((0,l.A)(e),"opened"),a.n=1,e.updateComplete;case 1:requestAnimationFrame((()=>{var a;null===(a=e.querySelector("[autofocus]"))||void 0===a||a.focus()}));case 2:return a.a(2)}}),a)}))),e._handleAfterShow=()=>{(0,f.r)((0,l.A)(e),"after-show")},e._handleAfterHide=()=>{e._open=!1,(0,f.r)((0,l.A)(e),"closed")},e}return(0,d.A)(a,e),(0,n.A)(a,[{key:"updated",value:function(e){(0,h.A)(a,"updated",this,3)([e]),e.has("open")&&(this._open=this.open)}},{key:"render",value:function(){var e,a;return(0,u.qy)(y||(y=$`
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
    `),this._open,!this.preventScrimClose,(0,v.J)(this.ariaLabelledBy||(void 0!==this.headerTitle?"ha-wa-dialog-title":void 0)),(0,v.J)(this.ariaDescribedBy),this._handleShow,this._handleAfterShow,this._handleAfterHide,this.headerSubtitlePosition,this._bodyScrolled,null!==(e=null===(a=this.hass)||void 0===a?void 0:a.localize("ui.common.close"))&&void 0!==e?e:"Close","M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",void 0!==this.headerTitle?(0,u.qy)(b||(b=$`<span slot="title" class="title" id="ha-wa-dialog-title">
                  ${0}
                </span>`),this.headerTitle):(0,u.qy)(x||(x=$`<slot name="headerTitle" slot="title"></slot>`)),void 0!==this.headerSubtitle?(0,u.qy)(_||(_=$`<span slot="subtitle">${0}</span>`),this.headerSubtitle):(0,u.qy)(k||(k=$`<slot name="headerSubtitle" slot="subtitle"></slot>`)),this._handleBodyScroll)}},{key:"disconnectedCallback",value:function(){(0,h.A)(a,"disconnectedCallback",this,3)([]),this._open=!1}},{key:"_handleBodyScroll",value:function(e){this._bodyScrolled=e.target.scrollTop>0}}])}(u.WF);C.styles=[w.dp,(0,u.AH)(A||(A=$`
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
    `))],(0,c.__decorate)([(0,g.MZ)({attribute:!1})],C.prototype,"hass",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"aria-labelledby"})],C.prototype,"ariaLabelledBy",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"aria-describedby"})],C.prototype,"ariaDescribedBy",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],C.prototype,"open",void 0),(0,c.__decorate)([(0,g.MZ)({reflect:!0})],C.prototype,"type",void 0),(0,c.__decorate)([(0,g.MZ)({type:String,reflect:!0,attribute:"width"})],C.prototype,"width",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0,attribute:"prevent-scrim-close"})],C.prototype,"preventScrimClose",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"header-title"})],C.prototype,"headerTitle",void 0),(0,c.__decorate)([(0,g.MZ)({attribute:"header-subtitle"})],C.prototype,"headerSubtitle",void 0),(0,c.__decorate)([(0,g.MZ)({type:String,attribute:"header-subtitle-position"})],C.prototype,"headerSubtitlePosition",void 0),(0,c.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0,attribute:"flexcontent"})],C.prototype,"flexContent",void 0),(0,c.__decorate)([(0,g.wk)()],C.prototype,"_open",void 0),(0,c.__decorate)([(0,g.P)(".body")],C.prototype,"bodyContainer",void 0),(0,c.__decorate)([(0,g.wk)()],C.prototype,"_bodyScrolled",void 0),(0,c.__decorate)([(0,g.Ls)({passive:!0})],C.prototype,"_handleBodyScroll",null),C=(0,c.__decorate)([(0,g.EM)("ha-wa-dialog")],C),a()}catch(D){a(D)}}))},89194:function(e,a,t){t.a(e,(async function(e,i){try{t.r(a);var o=t(44734),r=t(56038),n=t(69683),l=t(6454),s=(t(28706),t(62826)),d=t(96196),h=t(77845),c=t(92542),p=(t(86451),t(60733),t(28608),t(42921),t(23897),t(60961),t(36626)),u=t(54167),g=e([p,u]);[p,u]=g.then?(await g)():g;var v,f=e=>e,w=function(e){function a(){var e;(0,o.A)(this,a);for(var t=arguments.length,i=new Array(t),r=0;r<t;r++)i[r]=arguments[r];return(e=(0,n.A)(this,a,[].concat(i)))._opened=!1,e}return(0,l.A)(a,e),(0,r.A)(a,[{key:"showDialog",value:function(e){this._params=e,this._opened=!0}},{key:"closeDialog",value:function(){return this._opened=!1,!0}},{key:"_dialogClosed",value:function(){(0,c.r)(this,"dialog-closed",{dialog:this.localName}),this._params=void 0}},{key:"render",value:function(){return this._params?(0,d.qy)(v||(v=f`
      <ha-wa-dialog
        .hass=${0}
        .open=${0}
        header-title=${0}
        header-subtitle=${0}
        @closed=${0}
      >
        <ha-target-picker-item-row
          .hass=${0}
          .type=${0}
          .itemId=${0}
          .deviceFilter=${0}
          .entityFilter=${0}
          .includeDomains=${0}
          .includeDeviceClasses=${0}
          expand
        ></ha-target-picker-item-row>
      </ha-wa-dialog>
    `),this.hass,this._opened,this.hass.localize("ui.components.target-picker.target_details"),`${this.hass.localize(`ui.components.target-picker.type.${this._params.type}`)}:\n            ${this._params.title}`,this._dialogClosed,this.hass,this._params.type,this._params.itemId,this._params.deviceFilter,this._params.entityFilter,this._params.includeDomains,this._params.includeDeviceClasses):d.s6}}])}(d.WF);(0,s.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,s.__decorate)([(0,h.wk)()],w.prototype,"_params",void 0),(0,s.__decorate)([(0,h.wk)()],w.prototype,"_opened",void 0),w=(0,s.__decorate)([(0,h.EM)("ha-dialog-target-details")],w),i()}catch(m){i(m)}}))},99793:function(e,a,t){var i,o=t(96196);a.A=(0,o.AH)(i||(i=(e=>e)`:host {
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
`))},93900:function(e,a,t){t.a(e,(async function(e,a){try{var i=t(78261),o=t(61397),r=t(50264),n=t(44734),l=t(56038),s=t(69683),d=t(6454),h=t(25460),c=(t(27495),t(90906),t(96196)),p=t(77845),u=t(94333),g=t(32288),v=t(17051),f=t(42462),w=t(28438),m=t(98779),y=t(27259),b=t(31247),x=t(97039),_=t(92070),k=t(9395),A=t(32510),$=t(17060),C=t(88496),D=t(99793),S=e([C,$]);[C,$]=S.then?(await S)():S;var L,M,q,Z=e=>e,B=Object.defineProperty,z=Object.getOwnPropertyDescriptor,P=(e,a,t,i)=>{for(var o,r=i>1?void 0:i?z(a,t):a,n=e.length-1;n>=0;n--)(o=e[n])&&(r=(i?o(a,t,r):o(r))||r);return i&&r&&B(a,t,r),r},E=function(e){function a(){var e;return(0,n.A)(this,a),(e=(0,s.A)(this,a,arguments)).localize=new $.c(e),e.hasSlotController=new _.X(e,"footer","header-actions","label"),e.open=!1,e.label="",e.withoutHeader=!1,e.lightDismiss=!1,e.handleDocumentKeyDown=a=>{"Escape"===a.key&&e.open&&(a.preventDefault(),a.stopPropagation(),e.requestClose(e.dialog))},e}return(0,d.A)(a,e),(0,l.A)(a,[{key:"firstUpdated",value:function(){this.open&&(this.addOpenListeners(),this.dialog.showModal(),(0,x.JG)(this))}},{key:"disconnectedCallback",value:function(){(0,h.A)(a,"disconnectedCallback",this,3)([]),(0,x.I7)(this),this.removeOpenListeners()}},{key:"requestClose",value:(p=(0,r.A)((0,o.A)().m((function e(a){var t,i;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(t=new w.L({source:a}),this.dispatchEvent(t),!t.defaultPrevented){e.n=1;break}return this.open=!0,(0,y.Ud)(this.dialog,"pulse"),e.a(2);case 1:return this.removeOpenListeners(),e.n=2,(0,y.Ud)(this.dialog,"hide");case 2:this.open=!1,this.dialog.close(),(0,x.I7)(this),"function"==typeof(null==(i=this.originalTrigger)?void 0:i.focus)&&setTimeout((()=>i.focus())),this.dispatchEvent(new v.Z);case 3:return e.a(2)}}),e,this)}))),function(e){return p.apply(this,arguments)})},{key:"addOpenListeners",value:function(){document.addEventListener("keydown",this.handleDocumentKeyDown)}},{key:"removeOpenListeners",value:function(){document.removeEventListener("keydown",this.handleDocumentKeyDown)}},{key:"handleDialogCancel",value:function(e){e.preventDefault(),this.dialog.classList.contains("hide")||e.target!==this.dialog||this.requestClose(this.dialog)}},{key:"handleDialogClick",value:function(e){var a=e.target.closest('[data-dialog="close"]');a&&(e.stopPropagation(),this.requestClose(a))}},{key:"handleDialogPointerDown",value:(i=(0,r.A)((0,o.A)().m((function e(a){return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(a.target!==this.dialog){e.n=2;break}if(!this.lightDismiss){e.n=1;break}this.requestClose(this.dialog),e.n=2;break;case 1:return e.n=2,(0,y.Ud)(this.dialog,"pulse");case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"handleOpenChange",value:function(){this.open&&!this.dialog.open?this.show():!this.open&&this.dialog.open&&(this.open=!0,this.requestClose(this.dialog))}},{key:"show",value:(t=(0,r.A)((0,o.A)().m((function e(){var a;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(a=new m.k,this.dispatchEvent(a),!a.defaultPrevented){e.n=1;break}return this.open=!1,e.a(2);case 1:return this.addOpenListeners(),this.originalTrigger=document.activeElement,this.open=!0,this.dialog.showModal(),(0,x.JG)(this),requestAnimationFrame((()=>{var e=this.querySelector("[autofocus]");e&&"function"==typeof e.focus?e.focus():this.dialog.focus()})),e.n=2,(0,y.Ud)(this.dialog,"show");case 2:this.dispatchEvent(new f.q);case 3:return e.a(2)}}),e,this)}))),function(){return t.apply(this,arguments)})},{key:"render",value:function(){var e,a=!this.withoutHeader,t=this.hasSlotController.test("footer");return(0,c.qy)(L||(L=Z`
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
    `),null!==(e=this.ariaLabelledby)&&void 0!==e?e:"title",(0,g.J)(this.ariaDescribedby),(0,u.H)({dialog:!0,open:this.open}),this.handleDialogCancel,this.handleDialogClick,this.handleDialogPointerDown,a?(0,c.qy)(M||(M=Z`
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
            `),this.label.length>0?this.label:String.fromCharCode(8203),(e=>this.requestClose(e.target)),this.localize.term("close")):"",t?(0,c.qy)(q||(q=Z`
              <footer part="footer" class="footer">
                <slot name="footer"></slot>
              </footer>
            `)):"")}}]);var t,i,p}(A.A);E.css=D.A,P([(0,p.P)(".dialog")],E.prototype,"dialog",2),P([(0,p.MZ)({type:Boolean,reflect:!0})],E.prototype,"open",2),P([(0,p.MZ)({reflect:!0})],E.prototype,"label",2),P([(0,p.MZ)({attribute:"without-header",type:Boolean,reflect:!0})],E.prototype,"withoutHeader",2),P([(0,p.MZ)({attribute:"light-dismiss",type:Boolean})],E.prototype,"lightDismiss",2),P([(0,p.MZ)({attribute:"aria-labelledby"})],E.prototype,"ariaLabelledby",2),P([(0,p.MZ)({attribute:"aria-describedby"})],E.prototype,"ariaDescribedby",2),P([(0,k.w)("open",{waitUntilFirstUpdate:!0})],E.prototype,"handleOpenChange",1),E=P([(0,p.EM)("wa-dialog")],E),document.addEventListener("click",(e=>{var a=e.target.closest("[data-dialog]");if(a instanceof Element){var t=(0,b.v)(a.getAttribute("data-dialog")||""),o=(0,i.A)(t,2),r=o[0],n=o[1];if("open"===r&&null!=n&&n.length){var l=a.getRootNode().getElementById(n);"wa-dialog"===(null==l?void 0:l.localName)?l.open=!0:console.warn(`A dialog with an ID of "${n}" could not be found in this document.`)}}})),c.S$||document.addEventListener("pointerdown",(()=>{})),a()}catch(I){a(I)}}))}}]);
//# sourceMappingURL=7911.90dd4953f1d26c01.js.map