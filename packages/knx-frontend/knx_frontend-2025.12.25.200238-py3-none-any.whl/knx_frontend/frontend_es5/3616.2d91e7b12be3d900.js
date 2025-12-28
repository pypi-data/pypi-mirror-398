"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3616"],{16857:function(e,t,i){var o,r,n=i(44734),a=i(56038),c=i(69683),s=i(6454),l=i(25460),d=(i(28706),i(18111),i(7588),i(2892),i(26099),i(23500),i(62826)),h=i(96196),u=i(77845),p=i(76679),m=(i(41742),i(1554),e=>e),v=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(o))).corner="BOTTOM_START",e.menuCorner="START",e.x=null,e.y=null,e.multi=!1,e.activatable=!1,e.disabled=!1,e.fixed=!1,e.noAnchor=!1,e}return(0,s.A)(t,e),(0,a.A)(t,[{key:"items",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.items}},{key:"selected",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.selected}},{key:"focus",value:function(){var e,t;null!==(e=this._menu)&&void 0!==e&&e.open?this._menu.focusItemAtIndex(0):null===(t=this._triggerButton)||void 0===t||t.focus()}},{key:"render",value:function(){return(0,h.qy)(o||(o=m`
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
    `),this._handleClick,this._setTriggerAria,this.corner,this.menuCorner,this.fixed,this.multi,this.activatable,this.y,this.x)}},{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),"rtl"===p.G.document.dir&&this.updateComplete.then((()=>{this.querySelectorAll("ha-list-item").forEach((e=>{var t=document.createElement("style");t.innerHTML="span.material-icons:first-of-type { margin-left: var(--mdc-list-item-graphic-margin, 32px) !important; margin-right: 0px !important;}",e.shadowRoot.appendChild(t)}))}))}},{key:"_handleClick",value:function(){this.disabled||(this._menu.anchor=this.noAnchor?null:this,this._menu.show())}},{key:"_triggerButton",get:function(){return this.querySelector('ha-icon-button[slot="trigger"], ha-button[slot="trigger"]')}},{key:"_setTriggerAria",value:function(){this._triggerButton&&(this._triggerButton.ariaHasPopup="menu")}}])}(h.WF);v.styles=(0,h.AH)(r||(r=m`
    :host {
      display: inline-block;
      position: relative;
    }
    ::slotted([disabled]) {
      color: var(--disabled-text-color);
    }
  `)),(0,d.__decorate)([(0,u.MZ)()],v.prototype,"corner",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:"menu-corner"})],v.prototype,"menuCorner",void 0),(0,d.__decorate)([(0,u.MZ)({type:Number})],v.prototype,"x",void 0),(0,d.__decorate)([(0,u.MZ)({type:Number})],v.prototype,"y",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"multi",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"activatable",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"disabled",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"fixed",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean,attribute:"no-anchor"})],v.prototype,"noAnchor",void 0),(0,d.__decorate)([(0,u.P)("ha-menu",!0)],v.prototype,"_menu",void 0),v=(0,d.__decorate)([(0,u.EM)("ha-button-menu")],v)},90832:function(e,t,i){var o,r,n=i(61397),a=i(50264),c=i(44734),s=i(56038),l=i(69683),d=i(6454),h=i(25460),u=(i(28706),i(62826)),p=i(36387),m=i(34875),v=i(7731),y=i(96196),g=i(77845),_=i(94333),f=i(92542),b=(i(70524),e=>e),k=function(e){function t(){var e;(0,c.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(o))).checkboxDisabled=!1,e.indeterminate=!1,e}return(0,d.A)(t,e),(0,s.A)(t,[{key:"onChange",value:(i=(0,a.A)((0,n.A)().m((function e(i){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:(0,h.A)(t,"onChange",this,3)([i]),(0,f.r)(this,i.type);case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"render",value:function(){var e={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},t=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():y.s6,r=this.hasMeta&&this.left?this.renderMeta():y.s6,n=this.renderRipple();return(0,y.qy)(o||(o=b` ${0} ${0} ${0}
      <span class=${0}>
        <ha-checkbox
          reducedTouchTarget
          tabindex=${0}
          .checked=${0}
          .indeterminate=${0}
          ?disabled=${0}
          @change=${0}
        >
        </ha-checkbox>
      </span>
      ${0} ${0}`),n,i,this.left?"":t,(0,_.H)(e),this.tabindex,this.selected,this.indeterminate,this.disabled||this.checkboxDisabled,this.onChange,this.left?t:"",r)}}]);var i}(p.h);k.styles=[v.R,m.R,(0,y.AH)(r||(r=b`
      :host {
        --mdc-theme-secondary: var(--primary-color);
      }

      :host([graphic="avatar"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="medium"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="large"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="control"]) .mdc-deprecated-list-item__graphic {
        margin-inline-end: var(--mdc-list-item-graphic-margin, 16px);
        margin-inline-start: 0px;
        direction: var(--direction);
      }
      .mdc-deprecated-list-item__meta {
        flex-shrink: 0;
        direction: var(--direction);
        margin-inline-start: auto;
        margin-inline-end: 0;
      }
      .mdc-deprecated-list-item__graphic {
        margin-top: var(--check-list-item-graphic-margin-top);
      }
      :host([graphic="icon"]) .mdc-deprecated-list-item__graphic {
        margin-inline-start: 0;
        margin-inline-end: var(--mdc-list-item-graphic-margin, 32px);
      }
    `))],(0,u.__decorate)([(0,g.MZ)({type:Boolean,attribute:"checkbox-disabled"})],k.prototype,"checkboxDisabled",void 0),(0,u.__decorate)([(0,g.MZ)({type:Boolean})],k.prototype,"indeterminate",void 0),k=(0,u.__decorate)([(0,g.EM)("ha-check-list-item")],k)},59827:function(e,t,i){i.r(t),i.d(t,{HaFormMultiSelect:function(){return b}});var o,r,n,a,c,s=i(94741),l=i(44734),d=i(56038),h=i(69683),u=i(6454),p=(i(78170),i(28706),i(2008),i(50113),i(74423),i(62062),i(18111),i(22489),i(20116),i(61701),i(5506),i(26099),i(62826)),m=i(96196),v=i(77845),y=i(92542),g=(i(16857),i(90832),i(70524),i(48543),i(60733),i(78740),i(63419),i(99892),e=>e);function _(e){return Array.isArray(e)?e[0]:e}function f(e){return Array.isArray(e)?e[1]||e[0]:e}var b=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,h.A)(this,t,[].concat(o))).disabled=!1,e._opened=!1,e}return(0,u.A)(t,e),(0,d.A)(t,[{key:"focus",value:function(){this._input&&this._input.focus()}},{key:"render",value:function(){var e=Array.isArray(this.schema.options)?this.schema.options:Object.entries(this.schema.options),t=this.data||[];return e.length<6?(0,m.qy)(o||(o=g`<div>
        ${0}${0}
      </div> `),this.label,e.map((e=>{var i=_(e);return(0,m.qy)(r||(r=g`
            <ha-formfield .label=${0}>
              <ha-checkbox
                .checked=${0}
                .value=${0}
                .disabled=${0}
                @change=${0}
              ></ha-checkbox>
            </ha-formfield>
          `),f(e),t.includes(i),i,this.disabled,this._valueChanged)}))):(0,m.qy)(n||(n=g`
      <ha-md-button-menu
        .disabled=${0}
        @opening=${0}
        @closing=${0}
        positioning="fixed"
      >
        <ha-textfield
          slot="trigger"
          .label=${0}
          .value=${0}
          .disabled=${0}
          tabindex="-1"
        ></ha-textfield>
        <ha-icon-button
          slot="trigger"
          .label=${0}
          .path=${0}
        ></ha-icon-button>
        ${0}
      </ha-md-button-menu>
    `),this.disabled,this._handleOpen,this._handleClose,this.label,t.map((t=>f(e.find((e=>_(e)===t)))||t)).join(", "),this.disabled,this.label,this._opened?"M7,15L12,10L17,15H7Z":"M7,10L12,15L17,10H7Z",e.map((e=>{var i=_(e),o=t.includes(i);return(0,m.qy)(a||(a=g`<ha-md-menu-item
            type="option"
            aria-checked=${0}
            .value=${0}
            .action=${0}
            .activated=${0}
            @click=${0}
            @keydown=${0}
            keep-open
          >
            <ha-checkbox
              slot="start"
              tabindex="-1"
              .checked=${0}
            ></ha-checkbox>
            ${0}
          </ha-md-menu-item>`),o,i,o?"remove":"add",o,this._toggleItem,this._keydown,o,f(e))})))}},{key:"_keydown",value:function(e){"Space"!==e.code&&"Enter"!==e.code||(e.preventDefault(),this._toggleItem(e))}},{key:"_toggleItem",value:function(e){var t,i=this.data||[];t="add"===e.currentTarget.action?[].concat((0,s.A)(i),[e.currentTarget.value]):i.filter((t=>t!==e.currentTarget.value)),(0,y.r)(this,"value-changed",{value:t})}},{key:"firstUpdated",value:function(){this.updateComplete.then((()=>{var e,t=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("ha-textfield"))||{},i=t.formElement,o=t.mdcRoot;i&&(i.style.textOverflow="ellipsis"),o&&(o.style.cursor="pointer")}))}},{key:"updated",value:function(e){e.has("schema")&&this.toggleAttribute("own-margin",Object.keys(this.schema.options).length>=6&&!!this.schema.required)}},{key:"_valueChanged",value:function(e){var t=e.target,i=t.value,o=t.checked;this._handleValueChanged(i,o)}},{key:"_handleValueChanged",value:function(e,t){var i;if(t)if(this.data){if(this.data.includes(e))return;i=[].concat((0,s.A)(this.data),[e])}else i=[e];else{if(!this.data.includes(e))return;i=this.data.filter((t=>t!==e))}(0,y.r)(this,"value-changed",{value:i})}},{key:"_handleOpen",value:function(e){e.stopPropagation(),this._opened=!0,this.toggleAttribute("opened",!0)}},{key:"_handleClose",value:function(e){e.stopPropagation(),this._opened=!1,this.toggleAttribute("opened",!1)}}])}(m.WF);b.styles=(0,m.AH)(c||(c=g`
    :host([own-margin]) {
      margin-bottom: 5px;
    }
    ha-md-button-menu {
      display: block;
      cursor: pointer;
    }
    ha-formfield {
      display: block;
      padding-right: 16px;
      padding-inline-end: 16px;
      padding-inline-start: initial;
      direction: var(--direction);
    }
    ha-textfield {
      display: block;
      width: 100%;
      pointer-events: none;
    }
    ha-icon-button {
      color: var(--input-dropdown-icon-color);
      position: absolute;
      right: 1em;
      top: 4px;
      cursor: pointer;
      inset-inline-end: 1em;
      inset-inline-start: initial;
      direction: var(--direction);
    }
    :host([opened]) ha-icon-button {
      color: var(--primary-color);
    }
    :host([opened]) ha-md-button-menu {
      --mdc-text-field-idle-line-color: var(--input-hover-line-color);
      --mdc-text-field-label-ink-color: var(--primary-color);
    }
  `)),(0,p.__decorate)([(0,v.MZ)({attribute:!1})],b.prototype,"schema",void 0),(0,p.__decorate)([(0,v.MZ)({attribute:!1})],b.prototype,"data",void 0),(0,p.__decorate)([(0,v.MZ)()],b.prototype,"label",void 0),(0,p.__decorate)([(0,v.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,p.__decorate)([(0,v.wk)()],b.prototype,"_opened",void 0),(0,p.__decorate)([(0,v.P)("ha-button-menu")],b.prototype,"_input",void 0),b=(0,p.__decorate)([(0,v.EM)("ha-form-multi_select")],b)},63419:function(e,t,i){var o,r=i(44734),n=i(56038),a=i(69683),c=i(6454),s=(i(28706),i(62826)),l=i(96196),d=i(77845),h=i(92542),u=(i(41742),i(25460)),p=i(26139),m=i(8889),v=i(63374),y=function(e){function t(){return(0,r.A)(this,t),(0,a.A)(this,t,arguments)}return(0,c.A)(t,e),(0,n.A)(t,[{key:"connectedCallback",value:function(){(0,u.A)(t,"connectedCallback",this,3)([]),this.addEventListener("close-menu",this._handleCloseMenu)}},{key:"_handleCloseMenu",value:function(e){var t,i;e.detail.reason.kind===v.fi.KEYDOWN&&e.detail.reason.key===v.NV.ESCAPE||null===(t=(i=e.detail.initiator).clickAction)||void 0===t||t.call(i,e.detail.initiator)}}])}(p.W1);y.styles=[m.R,(0,l.AH)(o||(o=(e=>e)`
      :host {
        --md-sys-color-surface-container: var(--card-background-color);
      }
    `))],y=(0,s.__decorate)([(0,d.EM)("ha-md-menu")],y);var g,_,f=e=>e,b=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,o=new Array(i),n=0;n<i;n++)o[n]=arguments[n];return(e=(0,a.A)(this,t,[].concat(o))).disabled=!1,e.anchorCorner="end-start",e.menuCorner="start-start",e.hasOverflow=!1,e.quick=!1,e}return(0,c.A)(t,e),(0,n.A)(t,[{key:"items",get:function(){return this._menu.items}},{key:"focus",value:function(){var e;this._menu.open?this._menu.focus():null===(e=this._triggerButton)||void 0===e||e.focus()}},{key:"render",value:function(){return(0,l.qy)(g||(g=f`
      <div @click=${0}>
        <slot name="trigger" @slotchange=${0}></slot>
      </div>
      <ha-md-menu
        .quick=${0}
        .positioning=${0}
        .hasOverflow=${0}
        .anchorCorner=${0}
        .menuCorner=${0}
        @opening=${0}
        @closing=${0}
      >
        <slot></slot>
      </ha-md-menu>
    `),this._handleClick,this._setTriggerAria,this.quick,this.positioning,this.hasOverflow,this.anchorCorner,this.menuCorner,this._handleOpening,this._handleClosing)}},{key:"_handleOpening",value:function(){(0,h.r)(this,"opening",void 0,{composed:!1})}},{key:"_handleClosing",value:function(){(0,h.r)(this,"closing",void 0,{composed:!1})}},{key:"_handleClick",value:function(){this.disabled||(this._menu.anchorElement=this,this._menu.open?this._menu.close():this._menu.show())}},{key:"_triggerButton",get:function(){return this.querySelector('ha-icon-button[slot="trigger"], ha-button[slot="trigger"], ha-assist-chip[slot="trigger"]')}},{key:"_setTriggerAria",value:function(){this._triggerButton&&(this._triggerButton.ariaHasPopup="menu")}}])}(l.WF);b.styles=(0,l.AH)(_||(_=f`
    :host {
      display: inline-block;
      position: relative;
    }
    ::slotted([disabled]) {
      color: var(--disabled-text-color);
    }
  `)),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,s.__decorate)([(0,d.MZ)()],b.prototype,"positioning",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:"anchor-corner"})],b.prototype,"anchorCorner",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:"menu-corner"})],b.prototype,"menuCorner",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"has-overflow"})],b.prototype,"hasOverflow",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],b.prototype,"quick",void 0),(0,s.__decorate)([(0,d.P)("ha-md-menu",!0)],b.prototype,"_menu",void 0),b=(0,s.__decorate)([(0,d.EM)("ha-md-button-menu")],b)},99892:function(e,t,i){var o,r=i(56038),n=i(44734),a=i(69683),c=i(6454),s=i(62826),l=i(54407),d=i(28522),h=i(96196),u=i(77845),p=function(e){function t(){return(0,n.A)(this,t),(0,a.A)(this,t,arguments)}return(0,c.A)(t,e),(0,r.A)(t)}(l.K);p.styles=[d.R,(0,h.AH)(o||(o=(e=>e)`
      :host {
        --ha-icon-display: block;
        --md-sys-color-primary: var(--primary-text-color);
        --md-sys-color-on-primary: var(--primary-text-color);
        --md-sys-color-secondary: var(--secondary-text-color);
        --md-sys-color-surface: var(--card-background-color);
        --md-sys-color-on-surface: var(--primary-text-color);
        --md-sys-color-on-surface-variant: var(--secondary-text-color);
        --md-sys-color-secondary-container: rgba(
          var(--rgb-primary-color),
          0.15
        );
        --md-sys-color-on-secondary-container: var(--text-primary-color);
        --mdc-icon-size: 16px;

        --md-sys-color-on-primary-container: var(--primary-text-color);
        --md-sys-color-on-secondary-container: var(--primary-text-color);
        --md-menu-item-label-text-font: Roboto, sans-serif;
      }
      :host(.warning) {
        --md-menu-item-label-text-color: var(--error-color);
        --md-menu-item-leading-icon-color: var(--error-color);
      }
      ::slotted([slot="headline"]) {
        text-wrap: nowrap;
      }
      :host([disabled]) {
        opacity: 1;
        --md-menu-item-label-text-color: var(--disabled-text-color);
        --md-menu-item-leading-icon-color: var(--disabled-text-color);
      }
    `))],(0,s.__decorate)([(0,u.MZ)({attribute:!1})],p.prototype,"clickAction",void 0),p=(0,s.__decorate)([(0,u.EM)("ha-md-menu-item")],p)}}]);
//# sourceMappingURL=3616.2d91e7b12be3d900.js.map