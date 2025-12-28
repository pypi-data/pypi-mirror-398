/*! For license information please see 5643.189e8dc038b941ba.js.LICENSE.txt */
export const __webpack_id__="5643";export const __webpack_ids__=["5643"];export const __webpack_modules__={48833:function(e,t,i){i.d(t,{P:()=>n});var o=i(58109),r=i(70076);const a=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"],n=e=>e.first_weekday===r.zt.language?"weekInfo"in Intl.Locale.prototype?new Intl.Locale(e.language).weekInfo.firstDay%7:(0,o.S)(e.language)%7:a.includes(e.first_weekday)?a.indexOf(e.first_weekday):1},77646:function(e,t,i){i.a(e,(async function(e,o){try{i.d(t,{K:()=>d});var r=i(22),a=i(22786),n=i(97518),s=e([r,n]);[r,n]=s.then?(await s)():s;const l=(0,a.A)((e=>new Intl.RelativeTimeFormat(e.language,{numeric:"auto"}))),d=(e,t,i,o=!0)=>{const r=(0,n.x)(e,i,t);return o?l(t).format(r.value,r.unit):Intl.NumberFormat(t.language,{style:"unit",unit:r.unit,unitDisplay:"long"}).format(Math.abs(r.value))};o()}catch(l){o(l)}}))},74522:function(e,t,i){i.d(t,{Z:()=>o});const o=e=>e.charAt(0).toUpperCase()+e.slice(1)},93777:function(e,t,i){i.d(t,{Y:()=>o});const o=(e,t="_")=>{const i="àáâäæãåāăąабçćčđďдèéêëēėęěеёэфğǵгḧхîïíīįìıİийкłлḿмñńǹňнôöòóœøōõőоṕпŕřрßśšşșсťțтûüùúūǘůűųувẃẍÿýыžźżз·",o=`aaaaaaaaaaabcccdddeeeeeeeeeeefggghhiiiiiiiiijkllmmnnnnnoooooooooopprrrsssssstttuuuuuuuuuuvwxyyyzzzz${t}`,r=new RegExp(i.split("").join("|"),"g"),a={"ж":"zh","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ю":"iu","я":"ia"};let n;return""===e?n="":(n=e.toString().toLowerCase().replace(r,(e=>o.charAt(i.indexOf(e)))).replace(/[а-я]/g,(e=>a[e]||"")).replace(/(\d),(?=\d)/g,"$1").replace(/[^a-z0-9]+/g,t).replace(new RegExp(`(${t})\\1+`,"g"),"$1").replace(new RegExp(`^${t}+`),"").replace(new RegExp(`${t}+$`),""),""===n&&(n="unknown")),n}},97518:function(e,t,i){i.a(e,(async function(e,o){try{i.d(t,{x:()=>p});var r=i(6946),a=i(52640),n=i(56232),s=i(48833);const d=1e3,c=60,h=60*c;function p(e,t=Date.now(),i,o={}){const l={...u,...o||{}},p=(+e-+t)/d;if(Math.abs(p)<l.second)return{value:Math.round(p),unit:"second"};const g=p/c;if(Math.abs(g)<l.minute)return{value:Math.round(g),unit:"minute"};const m=p/h;if(Math.abs(m)<l.hour)return{value:Math.round(m),unit:"hour"};const _=new Date(e),f=new Date(t);_.setHours(0,0,0,0),f.setHours(0,0,0,0);const b=(0,r.c)(_,f);if(0===b)return{value:Math.round(m),unit:"hour"};if(Math.abs(b)<l.day)return{value:b,unit:"day"};const v=(0,s.P)(i),x=(0,a.k)(_,{weekStartsOn:v}),y=(0,a.k)(f,{weekStartsOn:v}),k=(0,n.I)(x,y);if(0===k)return{value:b,unit:"day"};if(Math.abs(k)<l.week)return{value:k,unit:"week"};const w=_.getFullYear()-f.getFullYear(),$=12*w+_.getMonth()-f.getMonth();return 0===$?{value:k,unit:"week"}:Math.abs($)<l.month||0===w?{value:$,unit:"month"}:{value:Math.round(w),unit:"year"}}const u={second:59,minute:59,hour:22,day:5,week:4,month:11};o()}catch(l){o(l)}}))},17963:function(e,t,i){i.r(t);var o=i(62826),r=i(96196),a=i(77845),n=i(94333),s=i(92542);i(60733),i(60961);const l={info:"M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",warning:"M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",error:"M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z",success:"M20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4C12.76,4 13.5,4.11 14.2,4.31L15.77,2.74C14.61,2.26 13.34,2 12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"};class d extends r.WF{render(){return r.qy`
      <div
        class="issue-type ${(0,n.H)({[this.alertType]:!0})}"
        role="alert"
      >
        <div class="icon ${this.title?"":"no-title"}">
          <slot name="icon">
            <ha-svg-icon .path=${l[this.alertType]}></ha-svg-icon>
          </slot>
        </div>
        <div class=${(0,n.H)({content:!0,narrow:this.narrow})}>
          <div class="main-content">
            ${this.title?r.qy`<div class="title">${this.title}</div>`:r.s6}
            <slot></slot>
          </div>
          <div class="action">
            <slot name="action">
              ${this.dismissable?r.qy`<ha-icon-button
                    @click=${this._dismissClicked}
                    label="Dismiss alert"
                    .path=${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"}
                  ></ha-icon-button>`:r.s6}
            </slot>
          </div>
        </div>
      </div>
    `}_dismissClicked(){(0,s.r)(this,"alert-dismissed-clicked")}constructor(...e){super(...e),this.title="",this.alertType="info",this.dismissable=!1,this.narrow=!1}}d.styles=r.AH`
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
  `,(0,o.__decorate)([(0,a.MZ)()],d.prototype,"title",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"alert-type"})],d.prototype,"alertType",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],d.prototype,"dismissable",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],d.prototype,"narrow",void 0),d=(0,o.__decorate)([(0,a.EM)("ha-alert")],d)},89473:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(62826),r=i(88496),a=i(96196),n=i(77845),s=e([r]);r=(s.then?(await s)():s)[0];class l extends r.A{static get styles(){return[r.A.styles,a.AH`
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
      `]}constructor(...e){super(...e),this.variant="brand"}}l=(0,o.__decorate)([(0,n.EM)("ha-button")],l),t()}catch(l){t(l)}}))},95637:function(e,t,i){i.d(t,{l:()=>d});var o=i(62826),r=i(30728),a=i(47705),n=i(96196),s=i(77845);i(41742),i(60733);const l=["button","ha-list-item"],d=(e,t)=>n.qy`
  <div class="header_title">
    <ha-icon-button
      .label=${e?.localize("ui.common.close")??"Close"}
      .path=${"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"}
      dialogAction="close"
      class="header_button"
    ></ha-icon-button>
    <span>${t}</span>
  </div>
`;class c extends r.u{scrollToPos(e,t){this.contentElement?.scrollTo(e,t)}renderHeading(){return n.qy`<slot name="heading"> ${super.renderHeading()} </slot>`}firstUpdated(){super.firstUpdated(),this.suppressDefaultPressSelector=[this.suppressDefaultPressSelector,l].join(", "),this._updateScrolledAttribute(),this.contentElement?.addEventListener("scroll",this._onScroll,{passive:!0})}disconnectedCallback(){super.disconnectedCallback(),this.contentElement.removeEventListener("scroll",this._onScroll)}_updateScrolledAttribute(){this.contentElement&&this.toggleAttribute("scrolled",0!==this.contentElement.scrollTop)}constructor(...e){super(...e),this._onScroll=()=>{this._updateScrolledAttribute()}}}c.styles=[a.R,n.AH`
      :host([scrolled]) ::slotted(ha-dialog-header) {
        border-bottom: 1px solid
          var(--mdc-dialog-scroll-divider-color, rgba(0, 0, 0, 0.12));
      }
      .mdc-dialog {
        --mdc-dialog-scroll-divider-color: var(
          --dialog-scroll-divider-color,
          var(--divider-color)
        );
        z-index: var(--dialog-z-index, 8);
        -webkit-backdrop-filter: var(
          --ha-dialog-scrim-backdrop-filter,
          var(--dialog-backdrop-filter, none)
        );
        backdrop-filter: var(
          --ha-dialog-scrim-backdrop-filter,
          var(--dialog-backdrop-filter, none)
        );
        --mdc-dialog-box-shadow: var(--dialog-box-shadow, none);
        --mdc-typography-headline6-font-weight: var(--ha-font-weight-normal);
        --mdc-typography-headline6-font-size: 1.574rem;
      }
      .mdc-dialog__actions {
        justify-content: var(--justify-action-buttons, flex-end);
        padding: var(--ha-space-3) var(--ha-space-4) var(--ha-space-4)
          var(--ha-space-4);
      }
      .mdc-dialog__actions span:nth-child(1) {
        flex: var(--secondary-action-button-flex, unset);
      }
      .mdc-dialog__actions span:nth-child(2) {
        flex: var(--primary-action-button-flex, unset);
      }
      .mdc-dialog__container {
        align-items: var(--vertical-align-dialog, center);
        padding: var(--dialog-container-padding, var(--ha-space-0));
      }
      .mdc-dialog__title {
        padding: var(--ha-space-4) var(--ha-space-4) var(--ha-space-0)
          var(--ha-space-4);
      }
      .mdc-dialog__title:has(span) {
        padding: var(--ha-space-3) var(--ha-space-3) var(--ha-space-0);
      }
      .mdc-dialog__title::before {
        content: unset;
      }
      .mdc-dialog .mdc-dialog__content {
        position: var(--dialog-content-position, relative);
        padding: var(--dialog-content-padding, var(--ha-space-6));
      }
      :host([hideactions]) .mdc-dialog .mdc-dialog__content {
        padding-bottom: var(--dialog-content-padding, var(--ha-space-6));
      }
      .mdc-dialog .mdc-dialog__surface {
        position: var(--dialog-surface-position, relative);
        top: var(--dialog-surface-top);
        margin-top: var(--dialog-surface-margin-top);
        min-width: var(--mdc-dialog-min-width, auto);
        min-height: var(--mdc-dialog-min-height, auto);
        border-radius: var(
          --ha-dialog-border-radius,
          var(--ha-border-radius-3xl)
        );
        -webkit-backdrop-filter: var(--ha-dialog-surface-backdrop-filter, none);
        backdrop-filter: var(--ha-dialog-surface-backdrop-filter, none);
        background: var(
          --ha-dialog-surface-background,
          var(--mdc-theme-surface, #fff)
        );
        padding: var(--dialog-surface-padding, var(--ha-space-0));
      }
      :host([flexContent]) .mdc-dialog .mdc-dialog__content {
        display: flex;
        flex-direction: column;
      }

      .header_title {
        display: flex;
        align-items: center;
        direction: var(--direction);
      }
      .header_title span {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: block;
        padding-left: var(--ha-space-1);
        padding-right: var(--ha-space-1);
        margin-right: var(--ha-space-3);
        margin-inline-end: var(--ha-space-3);
        margin-inline-start: initial;
      }
      .header_button {
        text-decoration: none;
        color: inherit;
        inset-inline-start: initial;
        inset-inline-end: calc(var(--ha-space-3) * -1);
        direction: var(--direction);
      }
      .dialog-actions {
        inset-inline-start: initial !important;
        inset-inline-end: var(--ha-space-0) !important;
        direction: var(--direction);
      }
    `],c=(0,o.__decorate)([(0,s.EM)("ha-dialog")],c)},34811:function(e,t,i){i.d(t,{p:()=>d});var o=i(62826),r=i(96196),a=i(77845),n=i(94333),s=i(92542),l=i(99034);i(60961);class d extends r.WF{render(){const e=this.noCollapse?r.s6:r.qy`
          <ha-svg-icon
            .path=${"M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"}
            class="summary-icon ${(0,n.H)({expanded:this.expanded})}"
          ></ha-svg-icon>
        `;return r.qy`
      <div class="top ${(0,n.H)({expanded:this.expanded})}">
        <div
          id="summary"
          class=${(0,n.H)({noCollapse:this.noCollapse})}
          @click=${this._toggleContainer}
          @keydown=${this._toggleContainer}
          @focus=${this._focusChanged}
          @blur=${this._focusChanged}
          role="button"
          tabindex=${this.noCollapse?-1:0}
          aria-expanded=${this.expanded}
          aria-controls="sect1"
          part="summary"
        >
          ${this.leftChevron?e:r.s6}
          <slot name="leading-icon"></slot>
          <slot name="header">
            <div class="header">
              ${this.header}
              <slot class="secondary" name="secondary">${this.secondary}</slot>
            </div>
          </slot>
          ${this.leftChevron?r.s6:e}
          <slot name="icons"></slot>
        </div>
      </div>
      <div
        class="container ${(0,n.H)({expanded:this.expanded})}"
        @transitionend=${this._handleTransitionEnd}
        role="region"
        aria-labelledby="summary"
        aria-hidden=${!this.expanded}
        tabindex="-1"
      >
        ${this._showContent?r.qy`<slot></slot>`:""}
      </div>
    `}willUpdate(e){super.willUpdate(e),e.has("expanded")&&(this._showContent=this.expanded,setTimeout((()=>{this._container.style.overflow=this.expanded?"initial":"hidden"}),300))}_handleTransitionEnd(){this._container.style.removeProperty("height"),this._container.style.overflow=this.expanded?"initial":"hidden",this._showContent=this.expanded}async _toggleContainer(e){if(e.defaultPrevented)return;if("keydown"===e.type&&"Enter"!==e.key&&" "!==e.key)return;if(e.preventDefault(),this.noCollapse)return;const t=!this.expanded;(0,s.r)(this,"expanded-will-change",{expanded:t}),this._container.style.overflow="hidden",t&&(this._showContent=!0,await(0,l.E)());const i=this._container.scrollHeight;this._container.style.height=`${i}px`,t||setTimeout((()=>{this._container.style.height="0px"}),0),this.expanded=t,(0,s.r)(this,"expanded-changed",{expanded:this.expanded})}_focusChanged(e){this.noCollapse||this.shadowRoot.querySelector(".top").classList.toggle("focused","focus"===e.type)}constructor(...e){super(...e),this.expanded=!1,this.outlined=!1,this.leftChevron=!1,this.noCollapse=!1,this._showContent=this.expanded}}d.styles=r.AH`
    :host {
      display: block;
    }

    .top {
      display: flex;
      align-items: center;
      border-radius: var(--ha-card-border-radius, var(--ha-border-radius-lg));
    }

    .top.expanded {
      border-bottom-left-radius: 0px;
      border-bottom-right-radius: 0px;
    }

    .top.focused {
      background: var(--input-fill-color);
    }

    :host([outlined]) {
      box-shadow: none;
      border-width: 1px;
      border-style: solid;
      border-color: var(--outline-color);
      border-radius: var(--ha-card-border-radius, var(--ha-border-radius-lg));
    }

    .summary-icon {
      transition: transform 150ms cubic-bezier(0.4, 0, 0.2, 1);
      direction: var(--direction);
      margin-left: 8px;
      margin-inline-start: 8px;
      margin-inline-end: initial;
      border-radius: var(--ha-border-radius-circle);
    }

    #summary:focus-visible ha-svg-icon.summary-icon {
      background-color: var(--ha-color-fill-neutral-normal-active);
    }

    :host([left-chevron]) .summary-icon,
    ::slotted([slot="leading-icon"]) {
      margin-left: 0;
      margin-right: 8px;
      margin-inline-start: 0;
      margin-inline-end: 8px;
    }

    #summary {
      flex: 1;
      display: flex;
      padding: var(--expansion-panel-summary-padding, 0 8px);
      min-height: 48px;
      align-items: center;
      cursor: pointer;
      overflow: hidden;
      font-weight: var(--ha-font-weight-medium);
      outline: none;
    }
    #summary.noCollapse {
      cursor: default;
    }

    .summary-icon.expanded {
      transform: rotate(180deg);
    }

    .header,
    ::slotted([slot="header"]) {
      flex: 1;
      overflow-wrap: anywhere;
      color: var(--primary-text-color);
    }

    .container {
      padding: var(--expansion-panel-content-padding, 0 8px);
      overflow: hidden;
      transition: height 300ms cubic-bezier(0.4, 0, 0.2, 1);
      height: 0px;
    }

    .container.expanded {
      height: auto;
    }

    .secondary {
      display: block;
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s);
    }
  `,(0,o.__decorate)([(0,a.MZ)({type:Boolean,reflect:!0})],d.prototype,"expanded",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,reflect:!0})],d.prototype,"outlined",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"left-chevron",type:Boolean,reflect:!0})],d.prototype,"leftChevron",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"no-collapse",type:Boolean,reflect:!0})],d.prototype,"noCollapse",void 0),(0,o.__decorate)([(0,a.MZ)()],d.prototype,"header",void 0),(0,o.__decorate)([(0,a.MZ)()],d.prototype,"secondary",void 0),(0,o.__decorate)([(0,a.wk)()],d.prototype,"_showContent",void 0),(0,o.__decorate)([(0,a.P)(".container")],d.prototype,"_container",void 0),d=(0,o.__decorate)([(0,a.EM)("ha-expansion-panel")],d)},35150:function(e,t,i){i.r(t),i.d(t,{HaIconButtonToggle:()=>s});var o=i(62826),r=i(96196),a=i(77845),n=i(60733);class s extends n.HaIconButton{constructor(...e){super(...e),this.selected=!1}}s.styles=r.AH`
    :host {
      position: relative;
    }
    mwc-icon-button {
      position: relative;
      transition: color 180ms ease-in-out;
    }
    mwc-icon-button::before {
      opacity: 0;
      transition: opacity 180ms ease-in-out;
      background-color: var(--primary-text-color);
      border-radius: var(--ha-border-radius-2xl);
      height: 40px;
      width: 40px;
      content: "";
      position: absolute;
      top: -10px;
      left: -10px;
      bottom: -10px;
      right: -10px;
      margin: auto;
      box-sizing: border-box;
    }
    :host([border-only]) mwc-icon-button::before {
      background-color: transparent;
      border: 2px solid var(--primary-text-color);
    }
    :host([selected]) mwc-icon-button {
      color: var(--primary-background-color);
    }
    :host([selected]:not([disabled])) mwc-icon-button::before {
      opacity: 1;
    }
  `,(0,o.__decorate)([(0,a.MZ)({type:Boolean,reflect:!0})],s.prototype,"selected",void 0),s=(0,o.__decorate)([(0,a.EM)("ha-icon-button-toggle")],s)},56565:function(e,t,i){var o=i(62826),r=i(27686),a=i(7731),n=i(96196),s=i(77845);class l extends r.J{renderRipple(){return this.noninteractive?"":super.renderRipple()}static get styles(){return[a.R,n.AH`
        :host {
          padding-left: var(
            --mdc-list-side-padding-left,
            var(--mdc-list-side-padding, 20px)
          );
          padding-inline-start: var(
            --mdc-list-side-padding-left,
            var(--mdc-list-side-padding, 20px)
          );
          padding-right: var(
            --mdc-list-side-padding-right,
            var(--mdc-list-side-padding, 20px)
          );
          padding-inline-end: var(
            --mdc-list-side-padding-right,
            var(--mdc-list-side-padding, 20px)
          );
        }
        :host([graphic="avatar"]:not([twoLine])),
        :host([graphic="icon"]:not([twoLine])) {
          height: 48px;
        }
        span.material-icons:first-of-type {
          margin-inline-start: 0px !important;
          margin-inline-end: var(
            --mdc-list-item-graphic-margin,
            16px
          ) !important;
          direction: var(--direction) !important;
        }
        span.material-icons:last-of-type {
          margin-inline-start: auto !important;
          margin-inline-end: 0px !important;
          direction: var(--direction) !important;
        }
        .mdc-deprecated-list-item__meta {
          display: var(--mdc-list-item-meta-display);
          align-items: center;
          flex-shrink: 0;
        }
        :host([graphic="icon"]:not([twoline]))
          .mdc-deprecated-list-item__graphic {
          margin-inline-end: var(
            --mdc-list-item-graphic-margin,
            20px
          ) !important;
        }
        :host([multiline-secondary]) {
          height: auto;
        }
        :host([multiline-secondary]) .mdc-deprecated-list-item__text {
          padding: 8px 0;
        }
        :host([multiline-secondary]) .mdc-deprecated-list-item__secondary-text {
          text-overflow: initial;
          white-space: normal;
          overflow: auto;
          display: inline-block;
          margin-top: 10px;
        }
        :host([multiline-secondary]) .mdc-deprecated-list-item__primary-text {
          margin-top: 10px;
        }
        :host([multiline-secondary])
          .mdc-deprecated-list-item__secondary-text::before {
          display: none;
        }
        :host([multiline-secondary])
          .mdc-deprecated-list-item__primary-text::before {
          display: none;
        }
        :host([disabled]) {
          color: var(--disabled-text-color);
        }
        :host([noninteractive]) {
          pointer-events: unset;
        }
      `,"rtl"===document.dir?n.AH`
            span.material-icons:first-of-type,
            span.material-icons:last-of-type {
              direction: rtl !important;
              --direction: rtl;
            }
          `:n.AH``]}}l=(0,o.__decorate)([(0,s.EM)("ha-list-item")],l)},75261:function(e,t,i){var o=i(62826),r=i(70402),a=i(11081),n=i(77845);class s extends r.iY{}s.styles=a.R,s=(0,o.__decorate)([(0,n.EM)("ha-list")],s)},1554:function(e,t,i){var o=i(62826),r=i(43976),a=i(703),n=i(96196),s=i(77845),l=i(94333);i(75261);class d extends r.ZR{get listElement(){return this.listElement_||(this.listElement_=this.renderRoot.querySelector("ha-list")),this.listElement_}renderList(){const e="menu"===this.innerRole?"menuitem":"option",t=this.renderListClasses();return n.qy`<ha-list
      rootTabbable
      .innerAriaLabel=${this.innerAriaLabel}
      .innerRole=${this.innerRole}
      .multi=${this.multi}
      class=${(0,l.H)(t)}
      .itemRoles=${e}
      .wrapFocus=${this.wrapFocus}
      .activatable=${this.activatable}
      @action=${this.onAction}
    >
      <slot></slot>
    </ha-list>`}}d.styles=a.R,d=(0,o.__decorate)([(0,s.EM)("ha-menu")],d)},18043:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(62826),r=i(25625),a=i(96196),n=i(77845),s=i(77646),l=i(74522),d=e([s]);s=(d.then?(await d)():d)[0];class c extends a.mN{disconnectedCallback(){super.disconnectedCallback(),this._clearInterval()}connectedCallback(){super.connectedCallback(),this.datetime&&this._startInterval()}createRenderRoot(){return this}firstUpdated(e){super.firstUpdated(e),this._updateRelative()}update(e){super.update(e),this._updateRelative()}_clearInterval(){this._interval&&(window.clearInterval(this._interval),this._interval=void 0)}_startInterval(){this._clearInterval(),this._interval=window.setInterval((()=>this._updateRelative()),6e4)}_updateRelative(){if(this.datetime){const e="string"==typeof this.datetime?(0,r.H)(this.datetime):this.datetime,t=(0,s.K)(e,this.hass.locale);this.innerHTML=this.capitalize?(0,l.Z)(t):t}else this.innerHTML=this.hass.localize("ui.components.relative_time.never")}constructor(...e){super(...e),this.capitalize=!1}}(0,o.__decorate)([(0,n.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,o.__decorate)([(0,n.MZ)({attribute:!1})],c.prototype,"datetime",void 0),(0,o.__decorate)([(0,n.MZ)({type:Boolean})],c.prototype,"capitalize",void 0),c=(0,o.__decorate)([(0,n.EM)("ha-relative-time")],c),t()}catch(c){t(c)}}))},7153:function(e,t,i){var o=i(62826),r=i(4845),a=i(49065),n=i(96196),s=i(77845),l=i(7647);class d extends r.U{firstUpdated(){super.firstUpdated(),this.addEventListener("change",(()=>{this.haptic&&(0,l.j)(this,"light")}))}constructor(...e){super(...e),this.haptic=!1}}d.styles=[a.R,n.AH`
      :host {
        --mdc-theme-secondary: var(--switch-checked-color);
      }
      .mdc-switch.mdc-switch--checked .mdc-switch__thumb {
        background-color: var(--switch-checked-button-color);
        border-color: var(--switch-checked-button-color);
      }
      .mdc-switch.mdc-switch--checked .mdc-switch__track {
        background-color: var(--switch-checked-track-color);
        border-color: var(--switch-checked-track-color);
      }
      .mdc-switch:not(.mdc-switch--checked) .mdc-switch__thumb {
        background-color: var(--switch-unchecked-button-color);
        border-color: var(--switch-unchecked-button-color);
      }
      .mdc-switch:not(.mdc-switch--checked) .mdc-switch__track {
        background-color: var(--switch-unchecked-track-color);
        border-color: var(--switch-unchecked-track-color);
      }
    `],(0,o.__decorate)([(0,s.MZ)({type:Boolean})],d.prototype,"haptic",void 0),d=(0,o.__decorate)([(0,s.EM)("ha-switch")],d)},7647:function(e,t,i){i.d(t,{j:()=>r});var o=i(92542);const r=(e,t)=>{(0,o.r)(e,"haptic",t)}},21912:function(e,t,i){i.d(t,{M:()=>o});const o=/(?:iphone|android|ipad)/i.test(navigator.userAgent)},80111:function(e,t,i){i.d(t,{C:()=>o});const o="ontouchstart"in window||navigator.maxTouchPoints>0||navigator.msMaxTouchPoints>0},7791:function(e,t,i){var o=i(62826),r=i(96196),a=i(77845),n=(i(60733),i(41508));class s extends n._{render(){return r.qy`
      <div class="container">
        <div class="content-wrapper">
          <slot name="primary"></slot>
          <slot name="secondary"></slot>
        </div>
        <!-- Filter Button - conditionally rendered based on filterValue and filterDisabled -->
        ${this.filterValue&&!this.filterDisabled?r.qy`
              <div class="filter-button ${this.filterActive?"filter-active":""}">
                <ha-icon-button
                  .path=${this.filterActive?"M21 8H3V6H21V8M13.81 16H10V18H13.09C13.21 17.28 13.46 16.61 13.81 16M18 11H6V13H18V11M21.12 15.46L19 17.59L16.88 15.46L15.47 16.88L17.59 19L15.47 21.12L16.88 22.54L19 20.41L21.12 22.54L22.54 21.12L20.41 19L22.54 16.88L21.12 15.46Z":"M6,13H18V11H6M3,6V8H21V6M10,18H14V16H10V18Z"}
                  @click=${this._handleFilterClick}
                  .title=${this.knx.localize(this.filterActive?"knx_table_cell_filterable_filter_remove_tooltip":"knx_table_cell_filterable_filter_set_tooltip",{value:this.filterDisplayText||this.filterValue})}
                >
                </ha-icon-button>
              </div>
            `:r.s6}
      </div>
    `}_handleFilterClick(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("toggle-filter",{bubbles:!0,composed:!0,detail:{value:this.filterValue,active:!this.filterActive}})),this.filterActive=!this.filterActive}constructor(...e){super(...e),this.filterActive=!1,this.filterDisabled=!1}}s.styles=[...n._.styles,r.AH`
      .filter-button {
        display: none;
        flex-shrink: 0;
      }
      .container:hover .filter-button {
        display: block;
      }
      .filter-active {
        display: block;
        color: var(--primary-color);
      }
    `],(0,o.__decorate)([(0,a.MZ)({type:Object})],s.prototype,"knx",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],s.prototype,"filterValue",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],s.prototype,"filterDisplayText",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],s.prototype,"filterActive",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],s.prototype,"filterDisabled",void 0),s=(0,o.__decorate)([(0,a.EM)("knx-table-cell-filterable")],s)},41508:function(e,t,i){i.d(t,{_:()=>n});var o=i(62826),r=i(96196),a=i(77845);class n extends r.WF{render(){return r.qy`
      <div class="container">
        <div class="content-wrapper">
          <slot name="primary"></slot>
          <slot name="secondary"></slot>
        </div>
      </div>
    `}}n.styles=[r.AH`
      :host {
        display: var(--knx-table-cell-display, block);
      }
      .container {
        padding: 4px 0;
        display: flex;
        align-items: center;
        flex-direction: row;
      }
      .content-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      ::slotted(*) {
        overflow: hidden;
        text-overflow: ellipsis;
      }
      ::slotted(.primary) {
        font-weight: 500;
        margin-bottom: 2px;
      }
      ::slotted(.secondary) {
        color: var(--secondary-text-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    `],n=(0,o.__decorate)([(0,a.EM)("knx-table-cell")],n)},1002:function(e,t,i){var o=i(62826),r=i(96196),a=i(77845),n=i(94333),s=i(58673),l=i(32288),d=i(4937),c=(i(70524),i(34811)),h=(i(60733),i(35150),i(60961),i(96270),i(39396)),p=i(92542);const u="asc",g=new Intl.Collator(void 0,{numeric:!0,sensitivity:"base"});class m extends c.p{}m.styles=r.AH`
    /* Inherit base styles */
    ${c.p.styles}

    /* Add specific styles for flex content */
    :host {
      display: flex;
      flex-direction: column;
      flex: 1;
      overflow: hidden;
    }

    .container.expanded {
      /* Keep original height: auto from base */
      /* Add requested styles */
      overflow: hidden !important;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
  `,m=(0,o.__decorate)([(0,a.EM)("flex-content-expansion-panel")],m);i(7153),i(1554),i(56565);class _ extends r.WF{get _ascendingText(){return this.ascendingText??this.knx?.localize("knx_sort_menu_item_ascending")??""}get _descendingText(){return this.descendingText??this.knx?.localize("knx_sort_menu_item_descending")??""}render(){return r.qy`
      <ha-list-item
        class="sort-row ${this.active?"active":""} ${this.disabled?"disabled":""}"
        @click=${this.disabled?r.s6:this._handleItemClick}
      >
        <div class="container">
          <div class="sort-field-name" title=${this.displayName} aria-label=${this.displayName}>
            ${this.displayName}
          </div>
          <div class="sort-buttons">
            ${this.isMobileDevice?this._renderMobileButtons():this._renderDesktopButtons()}
          </div>
        </div>
      </ha-list-item>
    `}_renderMobileButtons(){if(!this.active)return r.s6;const e=this.direction===f.DESC;return r.qy`
      <ha-icon-button
        class="active"
        .path=${e?this.descendingIcon:this.ascendingIcon}
        .label=${e?this._descendingText:this._ascendingText}
        .title=${e?this._descendingText:this._ascendingText}
        .disabled=${this.disabled}
        @click=${this.disabled?r.s6:this._handleMobileButtonClick}
      ></ha-icon-button>
    `}_renderDesktopButtons(){return r.qy`
      <ha-icon-button
        class=${this.active&&this.direction===f.DESC?"active":""}
        .path=${this.descendingIcon}
        .label=${this._descendingText}
        .title=${this._descendingText}
        .disabled=${this.disabled}
        @click=${this.disabled?r.s6:this._handleDescendingClick}
      ></ha-icon-button>
      <ha-icon-button
        class=${this.active&&this.direction===f.ASC?"active":""}
        .path=${this.ascendingIcon}
        .label=${this._ascendingText}
        .title=${this._ascendingText}
        .disabled=${this.disabled}
        @click=${this.disabled?r.s6:this._handleAscendingClick}
      ></ha-icon-button>
    `}_handleDescendingClick(e){e.stopPropagation(),(0,p.r)(this,"sort-option-selected",{criterion:this.criterion,direction:f.DESC})}_handleAscendingClick(e){e.stopPropagation(),(0,p.r)(this,"sort-option-selected",{criterion:this.criterion,direction:f.ASC})}_handleItemClick(){const e=this.active?this.direction===f.ASC?f.DESC:f.ASC:this.defaultDirection;(0,p.r)(this,"sort-option-selected",{criterion:this.criterion,direction:e})}_handleMobileButtonClick(e){e.stopPropagation();const t=this.direction===f.ASC?f.DESC:f.ASC;(0,p.r)(this,"sort-option-selected",{criterion:this.criterion,direction:t})}constructor(...e){super(...e),this.criterion="idField",this.displayName="",this.defaultDirection=f.DEFAULT_DIRECTION,this.direction=f.ASC,this.active=!1,this.ascendingIcon=_.DEFAULT_ASC_ICON,this.descendingIcon=_.DEFAULT_DESC_ICON,this.isMobileDevice=!1,this.disabled=!1}}_.DEFAULT_ASC_ICON="M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",_.DEFAULT_DESC_ICON="M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z",_.styles=r.AH`
    :host {
      display: block;
    }

    .sort-row {
      display: block;
      padding: 0 16px;
    }

    .sort-row.active {
      --mdc-theme-text-primary-on-background: var(--primary-color);
      background-color: var(--mdc-theme-surface-variant, rgba(var(--rgb-primary-color), 0.06));
      font-weight: 500;
    }

    .sort-row.disabled {
      opacity: 0.6;
      pointer-events: none;
    }

    .sort-row.disabled.active {
      --mdc-theme-text-primary-on-background: var(--primary-color);
      background-color: var(--mdc-theme-surface-variant, rgba(var(--rgb-primary-color), 0.06));
      font-weight: 500;
      opacity: 0.6;
    }

    .container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      height: 48px;
      gap: 10px;
    }

    .sort-field-name {
      display: flex;
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 1rem;
      align-items: center;
    }

    .sort-buttons {
      display: flex;
      align-items: center;
      min-width: 96px;
      justify-content: flex-end;
    }

    /* Hide sort buttons by default unless active */
    .sort-buttons ha-icon-button:not(.active) {
      display: none;
      color: var(--secondary-text-color);
    }

    /* Show sort buttons on row hover */
    .sort-row:hover .sort-buttons ha-icon-button {
      display: flex;
    }

    /* Don't show hover buttons when disabled */
    .sort-row.disabled:hover .sort-buttons ha-icon-button:not(.active) {
      display: none;
    }

    .sort-buttons ha-icon-button.active {
      display: flex;
      color: var(--primary-color);
    }

    /* Disabled buttons styling */
    .sort-buttons ha-icon-button[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .sort-buttons ha-icon-button.active[disabled] {
      --icon-primary-color: var(--primary-color);
      opacity: 0.6;
    }

    /* Mobile device specific styles */
    .sort-buttons ha-icon-button.mobile-button {
      display: flex;
      color: var(--primary-color);
    }
  `,(0,o.__decorate)([(0,a.MZ)({type:Object})],_.prototype,"knx",void 0),(0,o.__decorate)([(0,a.MZ)({type:String})],_.prototype,"criterion",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"display-name"})],_.prototype,"displayName",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"default-direction"})],_.prototype,"defaultDirection",void 0),(0,o.__decorate)([(0,a.MZ)({type:String})],_.prototype,"direction",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"active",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"ascending-text"})],_.prototype,"ascendingText",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"descending-text"})],_.prototype,"descendingText",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"ascending-icon"})],_.prototype,"ascendingIcon",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"descending-icon"})],_.prototype,"descendingIcon",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,attribute:"is-mobile-device"})],_.prototype,"isMobileDevice",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],_.prototype,"disabled",void 0),_=(0,o.__decorate)([(0,a.EM)("knx-sort-menu-item")],_);class f extends r.WF{updated(e){super.updated(e),(e.has("sortCriterion")||e.has("sortDirection")||e.has("isMobileDevice"))&&this._updateMenuItems()}_updateMenuItems(){this._sortMenuItems&&this._sortMenuItems.forEach((e=>{e.active=e.criterion===this.sortCriterion,e.direction=e.criterion===this.sortCriterion?this.sortDirection:e.defaultDirection,e.knx=this.knx,e.isMobileDevice=this.isMobileDevice}))}render(){return r.qy`
      <div class="menu-container">
        <ha-menu
          .corner=${"BOTTOM_START"}
          .fixed=${!0}
          @opened=${this._handleMenuOpened}
          @closed=${this._handleMenuClosed}
        >
          <slot name="header">
            <div class="header">
              <div class="title">
                <!-- Slot for custom title -->
                <slot name="title">${this.knx?.localize("knx_sort_menu_sort_by")??""}</slot>
              </div>
              <div class="toolbar">
                <!-- Slot for adding custom buttons to the header -->
                <slot name="toolbar"></slot>
              </div>
            </div>
            <li divider></li>
          </slot>

          <!-- Menu items will be slotted here -->
          <slot @sort-option-selected=${this._handleSortOptionSelected}></slot>
        </ha-menu>
      </div>
    `}openMenu(e){this._menu&&(this._menu.anchor=e,this._menu.show())}closeMenu(){this._menu&&this._menu.close()}_updateSorting(e,t){e===this.sortCriterion&&t===this.sortDirection||(this.sortCriterion=e,this.sortDirection=t,(0,p.r)(this,"sort-changed",{criterion:e,direction:t}))}_handleMenuOpened(){this._updateMenuItems()}_handleMenuClosed(){}_handleSortOptionSelected(e){const{criterion:t,direction:i}=e.detail;this._updateSorting(t,i),this.closeMenu()}constructor(...e){super(...e),this.sortCriterion="",this.sortDirection=f.DEFAULT_DIRECTION,this.isMobileDevice=!1}}f.ASC="asc",f.DESC="desc",f.DEFAULT_DIRECTION=f.ASC,f.styles=r.AH`
    .menu-container {
      position: relative;
      z-index: 1000;
      --mdc-list-vertical-padding: 0;
    }

    .header {
      position: sticky;
      top: 0;
      z-index: 1;
      background-color: var(--card-background-color, #fff);
      border-bottom: 1px solid var(--divider-color);
      font-weight: 500;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      height: 48px;
      gap: 20px;
      width: 100%;
      box-sizing: border-box;
    }

    .header .title {
      font-size: 14px;
      color: var(--secondary-text-color);
      font-weight: 500;
      flex: 1;
    }

    .header .toolbar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0px;
    }

    .menu-header .title {
      font-size: 14px;
      color: var(--secondary-text-color);
    }
  `,(0,o.__decorate)([(0,a.MZ)({type:Object})],f.prototype,"knx",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"sort-criterion"})],f.prototype,"sortCriterion",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"sort-direction"})],f.prototype,"sortDirection",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,attribute:"is-mobile-device"})],f.prototype,"isMobileDevice",void 0),(0,o.__decorate)([(0,a.P)("ha-menu")],f.prototype,"_menu",void 0),(0,o.__decorate)([(0,a.KN)({selector:"knx-sort-menu-item"})],f.prototype,"_sortMenuItems",void 0),f=(0,o.__decorate)([(0,a.EM)("knx-sort-menu")],f);class b extends r.WF{setHeight(e,t=!0){const i=Math.max(this.minHeight,Math.min(this.maxHeight,e));t?(this._isTransitioning=!0,this.height=i,setTimeout((()=>{this._isTransitioning=!1}),this.animationDuration)):this.height=i}expand(){this.setHeight(this.maxHeight)}collapse(){this.setHeight(this.minHeight)}toggle(){const e=this.minHeight+.5*(this.maxHeight-this.minHeight);this.height<=e?this.expand():this.collapse()}get expansionRatio(){return(this.height-this.minHeight)/(this.maxHeight-this.minHeight)}render(){return r.qy`
      <div
        class="separator-container ${this.customClass}"
        style="
          height: ${this.height}px;
          transition: ${this._isTransitioning?`height ${this.animationDuration}ms ease-in-out`:"none"};
        "
      >
        <div class="content">
          <slot></slot>
        </div>
      </div>
    `}constructor(...e){super(...e),this.height=1,this.maxHeight=50,this.minHeight=1,this.animationDuration=150,this.customClass="",this._isTransitioning=!1}}b.styles=r.AH`
    :host {
      display: block;
      width: 100%;
      position: relative;
    }

    .separator-container {
      width: 100%;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      background: var(--card-background-color, var(--primary-background-color));
    }

    .content {
      flex: 1;
      overflow: hidden;
      position: relative;
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
      .separator-container {
        transition: none !important;
      }
    }
  `,(0,o.__decorate)([(0,a.MZ)({type:Number,reflect:!0})],b.prototype,"height",void 0),(0,o.__decorate)([(0,a.MZ)({type:Number,attribute:"max-height"})],b.prototype,"maxHeight",void 0),(0,o.__decorate)([(0,a.MZ)({type:Number,attribute:"min-height"})],b.prototype,"minHeight",void 0),(0,o.__decorate)([(0,a.MZ)({type:Number,attribute:"animation-duration"})],b.prototype,"animationDuration",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"custom-class"})],b.prototype,"customClass",void 0),(0,o.__decorate)([(0,a.wk)()],b.prototype,"_isTransitioning",void 0),b=(0,o.__decorate)([(0,a.EM)("knx-separator")],b);class v extends r.WF{_computeFilterSortedOptions(){const e=this._computeFilteredOptions(),t=this._getComparator();return this._sortOptions(e,t,this.sortDirection)}_computeFilterSortedOptionsWithSeparator(){const e=this._computeFilteredOptions(),t=this._getComparator(),i=[],o=[];for(const r of e)r.selected?i.push(r):o.push(r);return{selected:this._sortOptions(i,t,this.sortDirection),unselected:this._sortOptions(o,t,this.sortDirection)}}_computeFilteredOptions(){const{data:e,config:{idField:t,primaryField:i,secondaryField:o,badgeField:r,custom:a},selectedOptions:n=[]}=this,s=e.map((e=>{const s=t.mapper(e),l=i.mapper(e);if(!s||!l)throw new Error("Missing id or primary field on item: "+JSON.stringify(e));const d={idField:s,primaryField:l,secondaryField:o.mapper(e),badgeField:r.mapper(e),selected:n.includes(s)};return a&&Object.entries(a).forEach((([t,i])=>{d[t]=i.mapper(e)})),d}));return this._applyFilterToOptions(s)}_getComparator(){const e=this._getFieldConfig(this.sortCriterion);return e?.comparator?e.comparator:this._generateComparator(this.sortCriterion)}_getFieldConfig(e){const{config:t}=this;return e in t&&"custom"!==e?t[e]:t.custom?.[e]}_generateComparator(e){return(t,i)=>{const o=this._compareByField(t,i,e);return 0!==o?o:this._lazyFallbackComparison(t,i,e)}}_lazyFallbackComparison(e,t,i){const o=this._getFallbackFields(i);for(const r of o){const i=this._compareByField(e,t,r);if(0!==i)return i}return this._compareByField(e,t,"idField")}_getFallbackFields(e){return{idField:[],primaryField:["secondaryField","badgeField"],secondaryField:["primaryField","badgeField"],badgeField:["primaryField","secondaryField"]}[e]||["primaryField"]}_compareByField(e,t,i){const o=e[i],r=t[i],a="string"==typeof o?o:o?.toString()??"",n="string"==typeof r?r:r?.toString()??"";return g.compare(a,n)}firstUpdated(){this._setupSeparatorScrollHandler()}updated(e){(e.has("expanded")||e.has("pinSelectedItems"))&&requestAnimationFrame((()=>{this._setupSeparatorScrollHandler(),(e.has("expanded")&&this.expanded||e.has("pinSelectedItems")&&this.pinSelectedItems)&&requestAnimationFrame((()=>{this._handleSeparatorScroll()}))}))}disconnectedCallback(){super.disconnectedCallback(),this._cleanupSeparatorScrollHandler()}_setupSeparatorScrollHandler(){this._cleanupSeparatorScrollHandler(),this._boundScrollHandler||(this._boundScrollHandler=this._handleSeparatorScroll.bind(this)),this.pinSelectedItems&&this._optionsListContainer&&this._optionsListContainer.addEventListener("scroll",this._boundScrollHandler,{passive:!0})}_cleanupSeparatorScrollHandler(){this._boundScrollHandler&&this._optionsListContainer&&this._optionsListContainer.removeEventListener("scroll",this._boundScrollHandler)}_handleSeparatorScroll(){if(!(this.pinSelectedItems&&this._separator&&this._optionsListContainer&&this._separatorContainer))return;const e=this._optionsListContainer.getBoundingClientRect(),t=this._separatorContainer.getBoundingClientRect().top-e.top,i=this._separatorScrollZone;if(t<=i&&t>=0){const e=1-t/i,o=this._separatorMinHeight+e*(this._separatorMaxHeight-this._separatorMinHeight);this._separator.setHeight(Math.round(o),!1)}else if(t>i){(this._separator.height||this._separatorMinHeight)!==this._separatorMinHeight&&this._separator.setHeight(this._separatorMinHeight,!1)}}_handleSeparatorClick(){this._optionsListContainer&&this._optionsListContainer.scrollTo({top:0,behavior:"smooth"})}_applyFilterToOptions(e){if(!this.filterQuery)return e;const t=this.filterQuery.toLowerCase(),{idField:i,primaryField:o,secondaryField:r,badgeField:a,custom:n}=this.config,s=[];return i.filterable&&s.push((e=>e.idField)),o.filterable&&s.push((e=>e.primaryField)),r.filterable&&s.push((e=>e.secondaryField)),a.filterable&&s.push((e=>e.badgeField)),n&&Object.entries(n).forEach((([e,t])=>{t.filterable&&s.push((t=>{const i=t[e];return"string"==typeof i?i:i?.toString()}))})),e.filter((e=>s.some((i=>{const o=i(e);return"string"==typeof o&&o.toLowerCase().includes(t)}))))}_sortOptions(e,t,i=u){const o=i===u?1:-1;return[...e].sort(((e,i)=>t(e,i)*o))}_handleSearchChange(e){this.filterQuery=e.detail.value}_handleSortButtonClick(e){e.stopPropagation();const t=this.shadowRoot?.querySelector("knx-sort-menu");t&&t.openMenu(e.currentTarget)}_handleSortChanged(e){this.sortCriterion=e.detail.criterion,this.sortDirection=e.detail.direction,(0,p.r)(this,"sort-changed",{criterion:this.sortCriterion,direction:this.sortDirection})}_handlePinButtonClick(e){e.stopPropagation(),this.pinSelectedItems=!this.pinSelectedItems}_handleClearFiltersButtonClick(e){e.stopPropagation(),e.preventDefault(),this._setSelectedOptions([])}_setSelectedOptions(e){this.selectedOptions=e,(0,p.r)(this,"selection-changed",{value:this.selectedOptions})}_getSortIcon(){return this.sortDirection===u?"M3 11H15V13H3M3 18V16H21V18M3 6H9V8H3Z":"M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"}_hasFilterableOrSortableFields(){if(!this.config)return!1;return[...Object.values(this.config).filter((e=>e&&"object"==typeof e&&"filterable"in e)),...this.config.custom?Object.values(this.config.custom):[]].some((e=>e.filterable||e.sortable))}_hasFilterableFields(){if(!this.config)return!1;return[...Object.values(this.config).filter((e=>e&&"object"==typeof e&&"filterable"in e)),...this.config.custom?Object.values(this.config.custom):[]].some((e=>e.filterable))}_hasSortableFields(){if(!this.config)return!1;return[...Object.values(this.config).filter((e=>e&&"object"==typeof e&&"sortable"in e)),...this.config.custom?Object.values(this.config.custom):[]].some((e=>e.sortable))}_expandedChanged(e){this.expanded=e.detail.expanded,(0,p.r)(this,"expanded-changed",{expanded:this.expanded})}_handleOptionItemClick(e){const t=e.currentTarget.getAttribute("data-value");t&&this._toggleOption(t)}_toggleOption(e){this.selectedOptions?.includes(e)?this._setSelectedOptions(this.selectedOptions?.filter((t=>t!==e))??[]):this._setSelectedOptions([...this.selectedOptions??[],e]),requestAnimationFrame((()=>{this._handleSeparatorScroll()}))}_renderFilterControl(){return r.qy`
      <div class="filter-toolbar">
        <div class="search">
          ${this._hasFilterableFields()?r.qy`
                <search-input-outlined
                  .hass=${this.hass}
                  .filter=${this.filterQuery}
                  @value-changed=${this._handleSearchChange}
                ></search-input-outlined>
              `:r.s6}
        </div>
        ${this._hasSortableFields()?r.qy`
              <div class="buttons">
                <ha-icon-button
                  class="sort-button"
                  .path=${this._getSortIcon()}
                  title=${this.sortDirection===u?this.knx.localize("knx_list_filter_sort_ascending_tooltip"):this.knx.localize("knx_list_filter_sort_descending_tooltip")}
                  @click=${this._handleSortButtonClick}
                ></ha-icon-button>

                <knx-sort-menu
                  .knx=${this.knx}
                  .sortCriterion=${this.sortCriterion}
                  .sortDirection=${this.sortDirection}
                  .isMobileDevice=${this.isMobileDevice}
                  @sort-changed=${this._handleSortChanged}
                >
                  <div slot="title">${this.knx.localize("knx_list_filter_sort_by")}</div>

                  <!-- Toolbar with additional controls like pin button -->
                  <div slot="toolbar">
                    <!-- Pin Button for keeping selected items at top -->
                    <ha-icon-button-toggle
                      .path=${"M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z"}
                      .selected=${this.pinSelectedItems}
                      @click=${this._handlePinButtonClick}
                      title=${this.knx.localize("knx_list_filter_selected_items_on_top")}
                    >
                    </ha-icon-button-toggle>
                  </div>

                  <!-- Sort menu items generated from all sortable fields -->
                  ${[...Object.entries(this.config||{}).filter((([e])=>"custom"!==e)).map((([e,t])=>({key:e,config:t}))),...Object.entries(this.config?.custom||{}).map((([e,t])=>({key:e,config:t})))].filter((({config:e})=>e.sortable)).map((({key:e,config:t})=>r.qy`
                        <knx-sort-menu-item
                          criterion=${e}
                          display-name=${(0,l.J)(t.fieldName)}
                          default-direction=${t.sortDefaultDirection??"asc"}
                          ascending-text=${t.sortAscendingText??this.knx.localize("knx_list_filter_sort_ascending")}
                          descending-text=${t.sortDescendingText??this.knx.localize("knx_list_filter_sort_descending")}
                          .disabled=${t.sortDisabled||!1}
                        ></knx-sort-menu-item>
                      `))}
                </knx-sort-menu>
              </div>
            `:r.s6}
      </div>
    `}_renderOptionsList(){return r.qy`
      ${(0,s.a)([this.filterQuery,this.sortDirection,this.sortCriterion,this.data,this.selectedOptions,this.expanded,this.config,this.pinSelectedItems],(()=>this.pinSelectedItems?this._renderPinnedOptionsList():this._renderRegularOptionsList()))}
    `}_renderPinnedOptionsList(){const e=this.knx.localize("knx_list_filter_no_results"),{selected:t,unselected:i}=this._computeFilterSortedOptionsWithSeparator();return 0===t.length&&0===i.length?r.qy`<div class="empty-message" role="alert">${e}</div>`:r.qy`
      <div class="options-list" tabindex="0">
        <!-- Render selected items first -->
        ${t.length>0?r.qy`
              ${(0,d.u)(t,(e=>e.idField),(e=>this._renderOptionItem(e)))}
            `:r.s6}

        <!-- Render separator between selected and unselected items -->
        ${t.length>0&&i.length>0?r.qy`
              <div class="separator-container">
                <knx-separator
                  .height=${this._separator?.height||this._separatorMinHeight}
                  .maxHeight=${this._separatorMaxHeight}
                  .minHeight=${this._separatorMinHeight}
                  .animationDuration=${this._separatorAnimationDuration}
                  customClass="list-separator"
                >
                  <div class="separator-content" @click=${this._handleSeparatorClick}>
                    <ha-svg-icon .path=${"M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z"}></ha-svg-icon>
                    <span class="separator-text">
                      ${this.knx.localize("knx_list_filter_scroll_to_selection")}
                    </span>
                  </div>
                </knx-separator>
              </div>
            `:r.s6}

        <!-- Render unselected items -->
        ${i.length>0?r.qy`
              ${(0,d.u)(i,(e=>e.idField),(e=>this._renderOptionItem(e)))}
            `:r.s6}
      </div>
    `}_renderRegularOptionsList(){const e=this.knx.localize("knx_list_filter_no_results"),t=this._computeFilterSortedOptions();return 0===t.length?r.qy`<div class="empty-message" role="alert">${e}</div>`:r.qy`
      <div class="options-list" tabindex="0">
        ${(0,d.u)(t,(e=>e.idField),(e=>this._renderOptionItem(e)))}
      </div>
    `}_renderOptionItem(e){const t={"option-item":!0,selected:e.selected};return r.qy`
      <div
        class=${(0,n.H)(t)}
        role="option"
        aria-selected=${e.selected}
        @click=${this._handleOptionItemClick}
        data-value=${e.idField}
      >
        <div class="option-content">
          <div class="option-primary">
            <span class="option-label" title=${e.primaryField}>${e.primaryField}</span>
            ${e.badgeField?r.qy`<span class="option-badge">${e.badgeField}</span>`:r.s6}
          </div>

          ${e.secondaryField?r.qy`
                <div class="option-secondary" title=${e.secondaryField}>
                  ${e.secondaryField}
                </div>
              `:r.s6}
        </div>

        <ha-checkbox
          .checked=${e.selected}
          .value=${e.idField}
          tabindex="-1"
          pointer-events="none"
        ></ha-checkbox>
      </div>
    `}render(){const e=this.selectedOptions?.length??0,t=this.filterTitle||this.knx.localize("knx_list_filter_title"),i=this.knx.localize("knx_list_filter_clear");return r.qy`
      <flex-content-expansion-panel
        leftChevron
        .expanded=${this.expanded}
        @expanded-changed=${this._expandedChanged}
      >
        <!-- Header with title and clear selection control -->
        <div slot="header" class="header">
          <span class="title">
            ${t}
            ${e?r.qy`<div class="badge">${e}</div>`:r.s6}
          </span>
          <div class="controls">
            ${e?r.qy`
                  <ha-icon-button
                    .path=${"M21 8H3V6H21V8M13.81 16H10V18H13.09C13.21 17.28 13.46 16.61 13.81 16M18 11H6V13H18V11M21.12 15.46L19 17.59L16.88 15.46L15.47 16.88L17.59 19L15.47 21.12L16.88 22.54L19 20.41L21.12 22.54L22.54 21.12L20.41 19L22.54 16.88L21.12 15.46Z"}
                    @click=${this._handleClearFiltersButtonClick}
                    .title=${i}
                  ></ha-icon-button>
                `:r.s6}
          </div>
        </div>

        <!-- Render filter content only when panel is expanded and visible -->
        ${this.expanded?r.qy`
              <div class="filter-content">
                ${this._hasFilterableOrSortableFields()?this._renderFilterControl():r.s6}
              </div>

              <!-- Filter options list - moved outside filter-content for proper sticky behavior -->
              <div class="options-list-wrapper ha-scrollbar">${this._renderOptionsList()}</div>
            `:r.s6}
      </flex-content-expansion-panel>
    `}static get styles(){return[h.dp,r.AH`
        :host {
          display: flex;
          flex-direction: column;
          border-bottom: 1px solid var(--divider-color);
        }
        :host([expanded]) {
          flex: 1;
          height: 0;
          overflow: hidden;
        }

        flex-content-expansion-panel {
          --ha-card-border-radius: 0;
          --expansion-panel-content-padding: 0;
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
        }

        .title {
          display: flex;
          align-items: center;
          font-weight: 500;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          margin-left: 8px;
          min-width: 20px;
          height: 20px;
          box-sizing: border-box;
          border-radius: 50%;
          font-weight: 500;
          font-size: 12px;
          background-color: var(--primary-color);
          line-height: 1;
          text-align: center;
          padding: 0 4px;
          color: var(--text-primary-color);
        }

        .controls {
          display: flex;
          align-items: center;
          margin-left: auto;
        }

        .header ha-icon-button {
          margin-inline-end: 4px;
        }

        .filter-content {
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
        }

        .options-list-wrapper {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
        }

        .options-list {
          display: block;
          padding: 0;
          flex: 1;
        }

        .filter-toolbar {
          display: flex;
          align-items: center;
          padding: 0px 8px;
          gap: 4px;
          border-bottom: 1px solid var(--divider-color);
        }

        .search {
          flex: 1;
        }

        .buttons:last-of-type {
          margin-right: -8px;
        }

        search-input-outlined {
          display: block;
          flex: 1;
          padding: 8px 0;
        }

        .option-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding-left: 16px;
          min-height: 48px;
          cursor: pointer;
          position: relative;
        }
        .option-item:hover {
          background-color: rgba(var(--rgb-primary-text-color), 0.04);
        }
        .option-item.selected {
          background-color: var(--mdc-theme-surface-variant, rgba(var(--rgb-primary-color), 0.06));
        }

        .option-content {
          display: flex;
          flex-direction: column;
          width: 100%;
          min-width: 0;
          height: 100%;
          line-height: normal;
        }

        .option-primary {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
          margin-bottom: 3px;
        }

        .option-label {
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .option-secondary {
          color: var(--secondary-text-color);
          font-size: 0.85em;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .option-badge {
          display: inline-flex;
          background-color: rgba(var(--rgb-primary-color), 0.15);
          color: var(--primary-color);
          font-weight: 500;
          font-size: 0.75em;
          padding: 1px 6px;
          border-radius: 10px;
          min-width: 20px;
          height: 16px;
          align-items: center;
          justify-content: center;
          margin-left: 8px;
          vertical-align: middle;
        }

        .empty-message {
          text-align: center;
          padding: 16px;
          color: var(--secondary-text-color);
        }

        /* Prevent checkbox from capturing clicks */
        ha-checkbox {
          pointer-events: none;
        }

        knx-sort-menu ha-icon-button-toggle {
          --mdc-icon-button-size: 36px; /* Default is 48px */
          --mdc-icon-size: 18px; /* Default is 24px */
          color: var(--secondary-text-color);
        }

        knx-sort-menu ha-icon-button-toggle[selected] {
          --primary-background-color: var(--primary-color);
          --primary-text-color: transparent;
        }

        /* Separator Styling */
        .separator-container {
          position: sticky;
          top: 0;
          z-index: 10;
          background: var(--card-background-color);
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .separator-content {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 6px;
          padding: 8px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          font-size: 0.8em;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s ease;
          user-select: none;
          box-sizing: border-box;
        }

        .separator-content:hover {
          opacity: 0.9;
        }

        .separator-content ha-svg-icon {
          --mdc-icon-size: 16px;
        }

        .separator-text {
          text-align: center;
        }

        .list-separator {
          position: relative;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        /* Enhanced separator visibility when scrolled */
        .options-list:not(:hover) .separator-container {
          transition: box-shadow 0.2s ease;
        }
      `]}constructor(...e){super(...e),this.data=[],this.expanded=!1,this.narrow=!1,this.pinSelectedItems=!0,this.filterQuery="",this.sortCriterion="primaryField",this.sortDirection="asc",this.isMobileDevice=!1,this._separatorMaxHeight=28,this._separatorMinHeight=2,this._separatorAnimationDuration=150,this._separatorScrollZone=28}}(0,o.__decorate)([(0,a.MZ)({attribute:!1,hasChanged:()=>!1})],v.prototype,"hass",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],v.prototype,"knx",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],v.prototype,"data",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],v.prototype,"selectedOptions",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],v.prototype,"config",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,reflect:!0})],v.prototype,"expanded",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean})],v.prototype,"narrow",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,attribute:"pin-selected-items"})],v.prototype,"pinSelectedItems",void 0),(0,o.__decorate)([(0,a.MZ)({type:String,attribute:"filter-title"})],v.prototype,"filterTitle",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"filter-query"})],v.prototype,"filterQuery",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"sort-criterion"})],v.prototype,"sortCriterion",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:"sort-direction"})],v.prototype,"sortDirection",void 0),(0,o.__decorate)([(0,a.MZ)({type:Boolean,attribute:"is-mobile-device"})],v.prototype,"isMobileDevice",void 0),(0,o.__decorate)([(0,a.P)("knx-separator")],v.prototype,"_separator",void 0),(0,o.__decorate)([(0,a.P)(".options-list-wrapper")],v.prototype,"_optionsListContainer",void 0),(0,o.__decorate)([(0,a.P)(".separator-container")],v.prototype,"_separatorContainer",void 0),v=(0,o.__decorate)([(0,a.EM)("knx-list-filter")],v)},31820:function(e,t,i){var o=i(62826),r=i(96196),a=i(77845);class n extends r.WF{render(){return r.qy`
      <header class="header">
        <div class="header-bar">
          <section class="header-navigation-icon">
            <slot name="navigationIcon"></slot>
          </section>
          <section class="header-content">
            <div class="header-title">
              <slot name="title"></slot>
            </div>
            <div class="header-subtitle">
              <slot name="subtitle"></slot>
            </div>
          </section>
          <section class="header-action-items">
            <slot name="actionItems"></slot>
          </section>
        </div>
        <slot></slot>
      </header>
    `}static get styles(){return[r.AH`
        :host {
          display: block;
        }
        :host([show-border]) {
          border-bottom: 1px solid var(--mdc-dialog-scroll-divider-color, rgba(0, 0, 0, 0.12));
        }
        .header-bar {
          display: flex;
          flex-direction: row;
          align-items: center;
          padding: 4px 24px 4px 24px;
          box-sizing: border-box;
          gap: 12px;
        }
        .header-content {
          flex: 1;
          padding: 10px 4px;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .header-title {
          font-size: 22px;
          line-height: 28px;
          font-weight: 400;
        }
        .header-subtitle {
          margin-top: 2px;
          font-size: 14px;
          color: var(--secondary-text-color);
        }

        .header-navigation-icon {
          flex: none;
          min-width: 8px;
          height: 100%;
          display: flex;
          flex-direction: row;
        }
        .header-action-items {
          flex: none;
          min-width: 8px;
          height: 100%;
          display: flex;
          flex-direction: row;
        }
      `]}constructor(...e){super(...e),this.showBorder=!1}}(0,o.__decorate)([(0,a.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],n.prototype,"showBorder",void 0),n=(0,o.__decorate)([(0,a.EM)("knx-dialog-header")],n)},10338:function(e,t,i){i.d(t,{K:()=>_});var o=i(5871),r=i(76679),a=i(22786),n=i(65294);class s{add(e){const t=Array.isArray(e)?e:[e];if(0===this._buffer.length)this._buffer.push(...t),t.length>1&&this._buffer.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0));else{const e=this._buffer[this._buffer.length-1].timestampIso,i=t.every((t=>t.timestampIso>=e)),o=t.length<=1||t.every(((e,i)=>0===i||t[i-1].timestampIso<=e.timestampIso));i&&o?this._buffer.push(...t):(this._buffer.push(...t),this._buffer.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0)))}if(this._buffer.length>this._maxSize){const e=this._buffer.length-this._maxSize;return this._buffer.splice(0,e)}return[]}merge(e){const t=new Set(this._buffer.map((e=>e.id))),i=e.filter((e=>!t.has(e.id)));i.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0));return{added:i,removed:this.add(i)}}setMaxSize(e){if(this._maxSize=e,this._buffer.length>e){const t=this._buffer.length-e;return this._buffer.splice(0,t)}return[]}get maxSize(){return this._maxSize}get length(){return this._buffer.length}get snapshot(){return[...this._buffer]}clear(){const e=[...this._buffer];return this._buffer.length=0,e}get isEmpty(){return 0===this._buffer.length}at(e){return this._buffer[e]}findIndexById(e){return this._buffer.findIndex((t=>t.id===e))}getById(e){return this._buffer.find((t=>t.id===e))}constructor(e=2e3){this._maxSize=e,this._buffer=[]}}var l=i(78577);const d=new l.Q("connection_service");class c{get connectionError(){return this._connectionError}get isConnected(){return!!this._subscribed}onTelegram(e){this._onTelegram=e}onConnectionChange(e){this._onConnectionChange=e}async subscribe(e){if(this._subscribed)d.warn("Already subscribed to telegrams");else try{this._subscribed=await(0,n.EE)(e,(e=>{this._onTelegram&&this._onTelegram(e)})),this._connectionError=null,this._notifyConnectionChange(!0),d.debug("Successfully subscribed to telegrams")}catch(t){throw d.error("Failed to subscribe to telegrams",t),this._connectionError=t instanceof Error?t.message:String(t),this._notifyConnectionChange(!1,this._connectionError),t}}unsubscribe(){this._subscribed&&(this._subscribed(),this._subscribed=void 0,this._notifyConnectionChange(!1),d.debug("Unsubscribed from telegrams"))}async reconnect(e){this._connectionError=null,this._notifyConnectionChange(!1),await this.subscribe(e)}clearError(){this._connectionError=null,this._notifyConnectionChange(this.isConnected)}disconnect(){this.unsubscribe(),this._onTelegram=null,this._onConnectionChange=null}_notifyConnectionChange(e,t){this._onConnectionChange&&this._onConnectionChange(e,t)}constructor(){this._connectionError=null,this._onTelegram=null,this._onConnectionChange=null}}var h=i(93777),p=i(25474);class u{constructor(e){this.offset=null,this.id=(0,h.Y)(`${e.timestamp}_${e.source}_${e.destination}`),this.timestampIso=e.timestamp,this.timestamp=new Date(e.timestamp),this.sourceAddress=e.source,this.sourceText=e.source_name,this.sourceName=`${e.source}: ${e.source_name}`,this.destinationAddress=e.destination,this.destinationText=e.destination_name,this.destinationName=`${e.destination}: ${e.destination_name}`,this.type=e.telegramtype,this.direction=e.direction,this.payload=p.e4.payload(e),this.dpt=p.e4.dptNameNumber(e),this.unit=e.unit,this.value=p.e4.valueWithUnit(e)||this.payload||("GroupValueRead"===e.telegramtype?"GroupRead":"")}}const g=new l.Q("group_monitor_controller"),m=["source","destination","direction","telegramtype"];class _{hostConnected(){this._setFiltersFromUrl()}hostDisconnected(){this._connectionService.disconnect()}async setup(e){if(!this._connectionService.isConnected&&await this._loadRecentTelegrams(e))try{await this._connectionService.subscribe(e)}catch(t){g.error("Failed to setup connection",t),this._connectionError=t instanceof Error?t.message:String(t),this.host.requestUpdate()}}get telegrams(){return this._telegramBuffer.snapshot}get selectedTelegramId(){return this._selectedTelegramId}set selectedTelegramId(e){this._selectedTelegramId=e,this.host.requestUpdate()}get filters(){return this._filters}get sortColumn(){return this._sortColumn}set sortColumn(e){this._sortColumn=e,this.host.requestUpdate()}get sortDirection(){return this._sortDirection}set sortDirection(e){this._sortDirection=e||"desc",this.host.requestUpdate()}get expandedFilter(){return this._expandedFilter}get isReloadEnabled(){return this._isReloadEnabled}get isPaused(){return this._isPaused}get isProjectLoaded(){return this._isProjectLoaded}get connectionError(){return this._connectionError}getFilteredTelegramsAndDistinctValues(){return this._getFilteredTelegramsAndDistinctValues(this._bufferVersion,JSON.stringify(this._filters),this._telegramBuffer.snapshot,this._distinctValues,this._sortColumn,this._sortDirection)}matchesActiveFilters(e){return Object.entries(this._filters).every((([t,i])=>{if(!i?.length)return!0;const o={source:e.sourceAddress,destination:e.destinationAddress,direction:e.direction,telegramtype:e.type};return i.includes(o[t]||"")}))}toggleFilterValue(e,t,i){const o=this._filters[e]??[];o.includes(t)?this._filters={...this._filters,[e]:o.filter((e=>e!==t))}:this._filters={...this._filters,[e]:[...o,t]},this._updateUrlFromFilters(i),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}setFilterFieldValue(e,t,i){this._filters={...this._filters,[e]:t},this._updateUrlFromFilters(i),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}clearFilters(e){this._filters={},this._updateUrlFromFilters(e),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}updateExpandedFilter(e,t){this._expandedFilter=t?e:this._expandedFilter===e?null:this._expandedFilter,this.host.requestUpdate()}async togglePause(){this._isPaused=!this._isPaused,this.host.requestUpdate()}async reload(e){await this._loadRecentTelegrams(e)}async retryConnection(e){await this._connectionService.reconnect(e)}clearTelegrams(){const e=this._createFilteredDistinctValues();this._telegramBuffer.clear(),this._resetDistinctValues(e),this._isReloadEnabled=!0,this.host.requestUpdate()}navigateTelegram(e,t){if(!this._selectedTelegramId)return;const i=t.findIndex((e=>e.id===this._selectedTelegramId))+e;i>=0&&i<t.length&&(this._selectedTelegramId=t[i].id,this.host.requestUpdate())}_calculateTelegramOffset(e,t){if(!t)return null;return(0,p.u_)(e.timestampIso)-(0,p.u_)(t.timestampIso)}_extractTelegramField(e,t){switch(t){case"source":return{id:e.sourceAddress,name:e.sourceText||""};case"destination":return{id:e.destinationAddress,name:e.destinationText||""};case"direction":return{id:e.direction,name:""};case"telegramtype":return{id:e.type,name:""};default:return null}}_addToDistinctValues(e){for(const t of m){const i=this._extractTelegramField(e,t);if(!i){g.warn(`Unknown field for distinct values: ${t}`);continue}const{id:o,name:r}=i;this._distinctValues[t][o]||(this._distinctValues[t][o]={id:o,name:r,totalCount:0}),this._distinctValues[t][o].totalCount++,""===this._distinctValues[t][o].name&&r&&(this._distinctValues[t][o].name=r)}this._bufferVersion++}_removeFromDistinctValues(e){if(0!==e.length){for(const t of e)for(const e of m){const i=this._extractTelegramField(t,e);if(!i)continue;const{id:o}=i,r=this._distinctValues[e][o];r&&(r.totalCount--,r.totalCount<=0&&delete this._distinctValues[e][o])}this._bufferVersion++}}_createFilteredDistinctValues(){const e={source:{},destination:{},direction:{},telegramtype:{}};for(const t of m){const i=this._filters[t];if(i?.length)for(const o of i){const i=this._distinctValues[t][o];e[t][o]={id:o,name:i?.name||"",totalCount:0}}}return e}_cleanupUnusedFilterValues(){let e=!1;for(const t of m){const i=this._filters[t]||[],o=this._distinctValues[t];for(const[r,a]of Object.entries(o))0!==a.totalCount||i.includes(r)||(delete this._distinctValues[t][r],e=!0)}e&&this._bufferVersion++}_resetDistinctValues(e){this._distinctValues=e?{source:{...e.source},destination:{...e.destination},direction:{...e.direction},telegramtype:{...e.telegramtype}}:{source:{},destination:{},direction:{},telegramtype:{}},this._bufferVersion++}_calculateTelegramStorageBuffer(e){const t=Math.ceil(.1*e),i=100*Math.ceil(t/100);return Math.max(i,_.MIN_TELEGRAM_STORAGE_BUFFER)}async _loadRecentTelegrams(e){try{const t=await(0,n.eq)(e);this._isProjectLoaded=t.project_loaded;const i=t.recent_telegrams.length,o=i+this._calculateTelegramStorageBuffer(i);if(this._telegramBuffer.maxSize!==o){const e=this._telegramBuffer.setMaxSize(o);e.length>0&&this._removeFromDistinctValues(e)}const r=t.recent_telegrams.map((e=>new u(e))),{added:a,removed:s}=this._telegramBuffer.merge(r);if(s.length>0&&this._removeFromDistinctValues(s),a.length>0)for(const e of a)this._addToDistinctValues(e);return null!==this._connectionError&&(this._connectionError=null),this._isReloadEnabled=!1,(a.length>0||null===this._connectionError)&&this.host.requestUpdate(),!0}catch(t){return g.error("getGroupMonitorInfo failed",t),this._connectionError=t instanceof Error?t.message:String(t),this.host.requestUpdate(),!1}}_handleIncomingTelegram(e){const t=new u(e);if(this._isPaused)this._isReloadEnabled||(this._isReloadEnabled=!0,this.host.requestUpdate());else{const e=this._telegramBuffer.add(t);e.length>0&&this._removeFromDistinctValues(e),this._addToDistinctValues(t),this.host.requestUpdate()}}_updateUrlFromFilters(e){if(!e)return void g.warn("Route not available, cannot update URL");const t=new URLSearchParams;Object.entries(this._filters).forEach((([e,i])=>{Array.isArray(i)&&i.length>0&&t.set(e,i.join(","))}));const i=t.toString()?`${e.prefix}${e.path}?${t.toString()}`:`${e.prefix}${e.path}`;(0,o.o)(decodeURIComponent(i),{replace:!0})}_setFiltersFromUrl(){const e=new URLSearchParams(r.G.location.search),t=e.get("source"),i=e.get("destination"),o=e.get("direction"),a=e.get("telegramtype");if(!(t||i||o||a))return;this._filters={source:t?t.split(","):[],destination:i?i.split(","):[],direction:o?o.split(","):[],telegramtype:a?a.split(","):[]};const n=this._createFilteredDistinctValues();this._resetDistinctValues(n),this.host.requestUpdate()}constructor(e){this._connectionService=new c,this._telegramBuffer=new s(2e3),this._selectedTelegramId=null,this._filters={},this._sortColumn="timestampIso",this._sortDirection="desc",this._expandedFilter="source",this._isReloadEnabled=!1,this._isPaused=!1,this._isProjectLoaded=void 0,this._connectionError=null,this._distinctValues={source:{},destination:{},direction:{},telegramtype:{}},this._bufferVersion=0,this._getFilteredTelegramsAndDistinctValues=(0,a.A)(((e,t,i,o,r,a)=>{const n=i.filter((e=>this.matchesActiveFilters(e)));r&&a&&n.sort(((e,t)=>{let i,o,n;switch(r){case"timestampIso":i=e.timestampIso,o=t.timestampIso;break;case"sourceAddress":i=e.sourceAddress,o=t.sourceAddress;break;case"destinationAddress":i=e.destinationAddress,o=t.destinationAddress;break;case"sourceText":i=e.sourceText||"",o=t.sourceText||"";break;case"destinationText":i=e.destinationText||"",o=t.destinationText||"";break;default:i=e[r]||"",o=t[r]||""}return n="string"==typeof i&&"string"==typeof o?i.localeCompare(o):i<o?-1:i>o?1:0,"asc"===a?n:-n}));const s={source:{},destination:{},direction:{},telegramtype:{}},l=Object.keys(o);for(const d of l)for(const[e,t]of Object.entries(o[d]))s[d][e]={id:t.id,name:t.name,totalCount:t.totalCount,filteredCount:0};for(let d=0;d<n.length;d++){const e=n[d];if("timestampIso"===r&&a||!r){let t=null;t="desc"===a&&r?d<n.length-1?n[d+1]:null:d>0?n[d-1]:null,e.offset=this._calculateTelegramOffset(e,t)}else e.offset=null;for(const t of l){const i=this._extractTelegramField(e,t);if(!i)continue;const{id:o}=i,r=s[t][o];r&&(r.filteredCount=(r.filteredCount||0)+1)}}return{filteredTelegrams:n,distinctValues:s}})),this.host=e,e.addController(this),this._connectionService.onTelegram((e=>this._handleIncomingTelegram(e))),this._connectionService.onConnectionChange(((e,t)=>{this._connectionError=t||null,this.host.requestUpdate()}))}}_.MIN_TELEGRAM_STORAGE_BUFFER=1e3},4597:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(62826),r=i(96196),a=i(77845),n=i(92542),s=i(39396),l=(i(60961),i(89473)),d=(i(31820),i(25474)),c=i(18043),h=(i(60733),i(95637),e([l,c]));[l,c]=h.then?(await h)():h;const p="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z",u="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z",g="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z";class m extends r.WF{connectedCallback(){super.connectedCallback(),this._handleKeyDown=this._handleKeyDown.bind(this),document.addEventListener("keydown",this._handleKeyDown)}disconnectedCallback(){document.removeEventListener("keydown",this._handleKeyDown),super.disconnectedCallback()}closeDialog(){this.telegram=void 0,(0,n.r)(this,"dialog-closed",{dialog:this.localName},{bubbles:!1})}_checkScrolled(e){const t=e.target,i=this.shadowRoot?.querySelector("knx-dialog-header");i&&t.scrollTop>0?i.showBorder=!0:i&&(i.showBorder=!1)}render(){if(!this.telegram)return this.closeDialog(),r.s6;const e="Outgoing"===this.telegram.direction?"outgoing":"incoming";return r.qy`
      <!-- 
        The .heading property is required for the header slot to be rendered,
        even though we override it with our custom knx-dialog-header component.
        The value is not displayed but must be truthy for the slot to work.
      -->
      <ha-dialog open @closed=${this.closeDialog} .heading=${" "}>
        <knx-dialog-header slot="heading" .showBorder=${!0}>
          <ha-icon-button
            slot="navigationIcon"
            .label=${this.knx.localize("ui.dialogs.generic.close")}
            .path=${g}
            dialogAction="close"
            class="close-button"
          ></ha-icon-button>
          <div slot="title" class="header-title">
            ${this.knx.localize("knx_telegram_info_dialog_telegram")}
          </div>
          <div slot="subtitle">
            <span title=${(0,d.CY)(this.telegram.timestampIso)}>
              ${(0,d.HF)(this.telegram.timestamp)+" "}
            </span>
            ${this.narrow?r.s6:r.qy`
                  (<ha-relative-time
                    .hass=${this.hass}
                    .datetime=${this.telegram.timestamp}
                    .capitalize=${!1}
                  ></ha-relative-time
                  >)
                `}
          </div>
          <div slot="actionItems" class="direction-badge ${e}">
            ${this.knx.localize(this.telegram.direction)}
          </div>
        </knx-dialog-header>
        <div class="content" @scroll=${this._checkScrolled}>
          <!-- Body: addresses + value + details -->
          <div class="telegram-body">
            <div class="addresses-row">
              <div class="address-item">
                <div class="item-label">
                  ${this.knx.localize("knx_telegram_info_dialog_source")}
                </div>
                <div class="address-chip">${this.telegram.sourceAddress}</div>
                ${this.telegram.sourceText?r.qy`<div class="item-name">${this.telegram.sourceText}</div>`:r.s6}
              </div>
              <div class="address-item">
                <div class="item-label">
                  ${this.knx.localize("knx_telegram_info_dialog_destination")}
                </div>
                <div class="address-chip">${this.telegram.destinationAddress}</div>
                ${this.telegram.destinationText?r.qy`<div class="item-name">${this.telegram.destinationText}</div>`:r.s6}
              </div>
            </div>

            ${null!=this.telegram.value?r.qy`
                  <div class="value-section">
                    <div class="value-label">
                      ${this.knx.localize("knx_telegram_info_dialog_value")}
                    </div>
                    <div class="value-content">${this.telegram.value}</div>
                  </div>
                `:r.s6}

            <div class="telegram-details">
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="detail-label">
                    ${this.knx.localize("knx_telegram_info_dialog_type")}
                  </div>
                  <div class="detail-value">${this.telegram.type}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-label">DPT</div>
                  <div class="detail-value">${this.telegram.dpt||""}</div>
                </div>
                ${null!=this.telegram.payload?r.qy`
                      <div class="detail-item payload">
                        <div class="detail-label">
                          ${this.knx.localize("knx_telegram_info_dialog_payload")}
                        </div>
                        <code>${this.telegram.payload}</code>
                      </div>
                    `:r.s6}
              </div>
            </div>
          </div>
        </div>

        <!-- Navigation buttons: previous / next -->
        <div slot="secondaryAction">
          <ha-button
            appearance="plain"
            @click=${this._previousTelegram}
            .disabled=${this.disablePrevious}
          >
            <ha-svg-icon .path=${p} slot="start"></ha-svg-icon>
            ${this.hass.localize("ui.common.previous")}
          </ha-button>
        </div>
        <div slot="primaryAction" class="primaryAction">
          <ha-button appearance="plain" @click=${this._nextTelegram} .disabled=${this.disableNext}>
            ${this.hass.localize("ui.common.next")}
            <ha-svg-icon .path=${u} slot="end"></ha-svg-icon>
          </ha-button>
        </div>
      </ha-dialog>
    `}_nextTelegram(){(0,n.r)(this,"next-telegram",void 0,{bubbles:!0})}_previousTelegram(){(0,n.r)(this,"previous-telegram",void 0,{bubbles:!0})}_handleKeyDown(e){if(this.telegram)switch(e.key){case"ArrowLeft":case"ArrowDown":this.disablePrevious||(e.preventDefault(),this._previousTelegram());break;case"ArrowRight":case"ArrowUp":this.disableNext||(e.preventDefault(),this._nextTelegram())}}static get styles(){return[s.nA,r.AH`
        ha-dialog {
          --vertical-align-dialog: center;
          --dialog-z-index: 20;
        }
        @media all and (max-width: 450px), all and (max-height: 500px) {
          /* When in fullscreen dialog should be attached to top */
          ha-dialog {
            --dialog-surface-margin-top: 0px;
            --dialog-content-padding: 16px 24px 16px 24px;
          }
        }
        @media all and (min-width: 600px) and (min-height: 501px) {
          /* Set the dialog width and min-height, but let height adapt to content */
          ha-dialog {
            --mdc-dialog-min-width: 580px;
            --mdc-dialog-max-width: 580px;
            --mdc-dialog-min-height: 70%;
            --mdc-dialog-max-height: 100%;
            --dialog-content-padding: 16px 24px 16px 24px;
          }
        }

        ha-button {
          --ha-button-radius: 8px; /* Default is --wa-border-radius-pill */
        }

        /* Custom heading styles */
        .custom-heading {
          display: flex;
          flex-direction: row;
          padding: 16px 24px 12px 16px;
          border-bottom: 1px solid var(--divider-color);
          align-items: center;
          gap: 12px;
        }
        .heading-content {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
        .header-title {
          margin: 0;
          font-size: 18px;
          font-weight: 500;
          line-height: 1.3;
          color: var(--primary-text-color);
        }
        .close-button {
          color: var(--primary-text-color);
          margin-right: -8px;
        }

        /* General content styling */
        .content {
          display: flex;
          flex-direction: column;
          flex: 1;
          gap: 16px;
          outline: none;
        }

        /* Timestamp style */
        .timestamp {
          font-size: 13px;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }
        .direction-badge {
          font-size: 12px;
          font-weight: 500;
          padding: 3px 10px;
          border-radius: 12px;
          text-transform: uppercase;
          letter-spacing: 0.4px;
          white-space: nowrap;
        }
        .direction-badge.outgoing {
          background-color: var(--knx-blue, var(--info-color));
          color: var(--text-primary-color, #fff);
        }
        .direction-badge.incoming {
          background-color: var(--knx-green, var(--success-color));
          color: var(--text-primary-color, #fff);
        }

        /* Body: addresses + value + details */
        .telegram-body {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .addresses-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }
        @media (max-width: 450px) {
          .addresses-row {
            grid-template-columns: 1fr;
            gap: 12px;
          }
        }
        .address-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
          background: var(--card-background-color);
          padding: 0px 12px 0px 12px;
          border-radius: 8px;
        }
        .item-label {
          font-size: 13px;
          font-weight: 500;
          color: var(--secondary-text-color);
          margin-bottom: 4px;
          letter-spacing: 0.5px;
        }
        .address-chip {
          font-family: var(--code-font-family, monospace);
          font-size: 16px;
          font-weight: 500;
          background: var(--secondary-background-color);
          border-radius: 12px;
          padding: 6px 12px;
          text-align: center;
          box-shadow: 0 1px 2px rgba(var(--rgb-primary-text-color), 0.06);
        }
        .item-name {
          font-size: 12px;
          color: var(--secondary-text-color);
          font-style: italic;
          margin-top: 4px;
          text-align: center;
        }

        /* Value section */
        .value-section {
          padding: 16px;
          background: var(--primary-background-color);
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(var(--rgb-primary-text-color), 0.06);
        }
        .value-label {
          font-size: 13px;
          color: var(--secondary-text-color);
          margin-bottom: 8px;
          font-weight: 500;
          letter-spacing: 0.4px;
        }
        .value-content {
          font-family: var(--code-font-family, monospace);
          font-size: 22px;
          font-weight: 600;
          color: var(--primary-color);
          text-align: center;
        }

        /* Telegram details (type/DPT/payload) */
        .telegram-details {
          padding: 16px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(var(--rgb-primary-text-color), 0.06);
        }
        .detail-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }
        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .detail-item.payload {
          grid-column: span 2;
          margin-top: 4px;
        }
        .detail-label {
          font-size: 13px;
          color: var(--secondary-text-color);
          font-weight: 500;
        }
        .detail-value {
          font-size: 14px;
          font-weight: 500;
        }
        code {
          font-family: var(--code-font-family, monospace);
          font-size: 13px;
          background: var(--card-background-color);
          padding: 8px 12px;
          border-radius: 6px;
          display: block;
          overflow-x: auto;
          white-space: pre;
          box-shadow: 0 1px 2px rgba(var(--rgb-primary-text-color), 0.04);
          margin-top: 4px;
        }

        .primaryAction {
          margin-right: 8px;
        }
      `]}constructor(...e){super(...e),this.narrow=!1,this.disableNext=!1,this.disablePrevious=!1}}(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"knx",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"narrow",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"telegram",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"disableNext",void 0),(0,o.__decorate)([(0,a.MZ)({attribute:!1})],m.prototype,"disablePrevious",void 0),m=(0,o.__decorate)([(0,a.EM)("knx-group-monitor-telegram-info-dialog")],m),t()}catch(p){t(p)}}))},84315:function(e,t,i){i.a(e,(async function(e,o){try{i.r(t),i.d(t,{KNXGroupMonitor:()=>x});var r=i(62826),a=i(96196),n=i(22786),s=i(54393),l=(i(98169),i(17963),i(89473)),d=(i(60733),i(21912)),c=i(80111),h=(i(41508),i(7791),i(4597)),p=(i(1002),i(77845)),u=i(25474),g=i(10338),m=e([s,l,h]);[s,l,h]=m.then?(await m)():m;const _="M15,16H19V18H15V16M15,8H22V10H15V8M15,12H21V14H15V12M3,18A2,2 0 0,0 5,20H11A2,2 0 0,0 13,18V8H3V18M14,5H11L10,4H6L5,5H2V7H14V5Z",f="M13,6V18L21.5,12M4,18L12.5,12L4,6V18Z",b="M14,19H18V5H14M6,19H10V5H6V19Z",v="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z";class x extends a.WF{static get styles(){return[a.AH`
        :host {
          --table-row-alternative-background-color: var(--primary-background-color);
        }

        ha-icon-button.active {
          color: var(--primary-color);
        }

        .table-header {
          border-bottom: 1px solid var(--divider-color);
          padding-bottom: 12px;
        }

        :host {
          --ha-data-table-row-style: {
            font-size: 0.9em;
            padding: 8px 0;
          };
        }

        .filter-wrapper {
          display: flex;
          flex-direction: column;
        }

        .toolbar-actions {
          padding-left: 8px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
      `]}get isMobileTouchDevice(){return d.M&&c.C}_getFilteredData(){return this.controller.getFilteredTelegramsAndDistinctValues()}async firstUpdated(){await this.controller.setup(this.hass)}get searchLabel(){if(this.narrow)return this.knx.localize("group_monitor_search_label_narrow");const{filteredTelegrams:e}=this._getFilteredData(),t=e.length,i=1===t?"group_monitor_search_label_singular":"group_monitor_search_label";return this.knx.localize(i,{count:t})}_hasActiveFilters(e){if(e){const t=this.controller.filters[e];return Array.isArray(t)&&t.length>0}return Object.values(this.controller.filters).some((e=>Array.isArray(e)&&e.length>0))}_handleSortingChanged({detail:{column:e,direction:t}}){this.controller.sortColumn=t?e:void 0,this.controller.sortDirection=t||void 0}_handleRowClick(e){this.controller.selectedTelegramId=e.detail.id}_handleDialogClosed(){this.controller.selectedTelegramId=null}async _handlePauseToggle(){await this.controller.togglePause()}async _handleReload(){await this.controller.reload(this.hass)}async _retryConnection(){await this.controller.retryConnection(this.hass)}_handleClearFilters(){this.controller.clearFilters(this.route)}_handleClearRows(){this.controller.clearTelegrams()}_selectNextTelegram(){const{filteredTelegrams:e}=this._getFilteredData();this.controller.navigateTelegram(1,e)}_selectPreviousTelegram(){const{filteredTelegrams:e}=this._getFilteredData();this.controller.navigateTelegram(-1,e)}_formatOffsetWithPrecision(e){if(null===e)return(0,u.RL)(e);return 0===Math.round(e/1e3)&&0!==e?(0,u.RL)(e,"microseconds"):(0,u.RL)(e,"milliseconds")}_renderTelegramInfoDialog(e){const{filteredTelegrams:t}=this._getFilteredData(),i=t.findIndex((t=>t.id===e)),o=t[i];return o?a.qy`
      <knx-group-monitor-telegram-info-dialog
        .hass=${this.hass}
        .knx=${this.knx}
        .narrow=${this.narrow}
        .telegram=${o}
        .disableNext=${i+1>=t.length}
        .disablePrevious=${i<=0}
        @next-telegram=${this._selectNextTelegram}
        @previous-telegram=${this._selectPreviousTelegram}
        @dialog-closed=${this._handleDialogClosed}
      >
      </knx-group-monitor-telegram-info-dialog>
    `:a.s6}render(){const e=Object.values(this.controller.filters).filter((e=>Array.isArray(e)&&e.length)).length,{filteredTelegrams:t,distinctValues:i}=this._getFilteredData();return a.qy`
      <hass-tabs-subpage-data-table
        .hass=${this.hass}
        .narrow=${this.narrow}
        .route=${this.route}
        .tabs=${this.tabs}
        main-page
        .columns=${this._columns(this.narrow,!0===this.controller.isProjectLoaded,this.hass.language)}
        .noDataText=${this.knx.localize("group_monitor_waiting_message")}
        .data=${t}
        .hasFab=${!1}
        .searchLabel=${this.searchLabel}
        .localizeFunc=${this.knx.localize}
        id="id"
        .clickable=${!0}
        .initialSorting=${{column:this.controller.sortColumn||"timestampIso",direction:this.controller.sortDirection||"desc"}}
        @row-click=${this._handleRowClick}
        @sorting-changed=${this._handleSortingChanged}
        has-filters
        .filters=${e}
        @clear-filter=${this._handleClearFilters}
      >
        <!-- Top header -->
        ${this.controller.connectionError?a.qy`
              <ha-alert
                slot="top-header"
                .alertType=${"error"}
                .title=${this.knx.localize("group_monitor_connection_error_title")}
              >
                ${this.controller.connectionError}
                <ha-button slot="action" @click=${this._retryConnection}>
                  ${this.knx.localize("group_monitor_retry_connection")}
                </ha-button>
              </ha-alert>
            `:a.s6}
        ${this.controller.isPaused?a.qy`
              <ha-alert
                slot="top-header"
                .alertType=${"info"}
                .dismissable=${!1}
                .title=${this.knx.localize("group_monitor_paused_title")}
              >
                ${this.knx.localize("group_monitor_paused_message")}
                <ha-button slot="action" @click=${this._handlePauseToggle}>
                  ${this.knx.localize("group_monitor_resume")}
                </ha-button>
              </ha-alert>
            `:""}
        ${!1===this.controller.isProjectLoaded?a.qy`
              <ha-alert
                slot="top-header"
                .alertType=${"info"}
                .dismissable=${!0}
                .title=${this.knx.localize("group_monitor_project_not_loaded_title")}
              >
                ${this.knx.localize("group_monitor_project_not_loaded_message")}
              </ha-alert>
            `:a.s6}

        <!-- Toolbar actions -->
        <div slot="toolbar-icon" class="toolbar-actions">
          <ha-icon-button
            .label=${this.controller.isPaused?this.knx.localize("group_monitor_resume"):this.knx.localize("group_monitor_pause")}
            .path=${this.controller.isPaused?f:b}
            class=${this.controller.isPaused?"active":""}
            @click=${this._handlePauseToggle}
            data-testid="pause-button"
            .title=${this.controller.isPaused?this.knx.localize("group_monitor_resume"):this.knx.localize("group_monitor_pause")}
          >
          </ha-icon-button>
          <ha-icon-button
            .label=${this.knx.localize("group_monitor_clear")}
            .path=${_}
            @click=${this._handleClearRows}
            ?disabled=${0===this.controller.telegrams.length}
            data-testid="clean-button"
            .title=${this.knx.localize("group_monitor_clear")}
          >
          </ha-icon-button>
          <ha-icon-button
            .label=${this.knx.localize("group_monitor_reload")}
            .path=${v}
            @click=${this._handleReload}
            ?disabled=${!this.controller.isReloadEnabled}
            data-testid="reload-button"
            .title=${this.knx.localize("group_monitor_reload")}
          >
          </ha-icon-button>
        </div>

        <!-- Filter for Source Address -->
        <knx-list-filter
          data-filter="source"
          slot="filter-pane"
          .hass=${this.hass}
          .knx=${this.knx}
          .data=${Object.values(i.source)}
          .config=${this._sourceFilterConfig(this._hasActiveFilters("source"),this.controller.filters.source?.length||0,this.sourceFilter?.sortCriterion,this.hass.language)}
          .selectedOptions=${this.controller.filters.source}
          .expanded=${"source"===this.controller.expandedFilter}
          .narrow=${this.narrow}
          .isMobileDevice=${this.isMobileTouchDevice}
          .filterTitle=${this.knx.localize("group_monitor_source")}
          @selection-changed=${this._handleSourceFilterChange}
          @expanded-changed=${this._handleSourceFilterExpanded}
          @sort-changed=${this._handleFilterSortChanged}
        ></knx-list-filter>

        <!-- Filter for Destination Address -->
        <knx-list-filter
          data-filter="destination"
          slot="filter-pane"
          .hass=${this.hass}
          .knx=${this.knx}
          .data=${Object.values(i.destination)}
          .config=${this._destinationFilterConfig(this._hasActiveFilters("destination"),this.controller.filters.destination?.length||0,this.destinationFilter?.sortCriterion,this.hass.language)}
          .selectedOptions=${this.controller.filters.destination}
          .expanded=${"destination"===this.controller.expandedFilter}
          .narrow=${this.narrow}
          .isMobileDevice=${this.isMobileTouchDevice}
          .filterTitle=${this.knx.localize("group_monitor_destination")}
          @selection-changed=${this._handleDestinationFilterChange}
          @expanded-changed=${this._handleDestinationFilterExpanded}
          @sort-changed=${this._handleFilterSortChanged}
        ></knx-list-filter>

        <!-- Filter for Direction -->
        <knx-list-filter
          slot="filter-pane"
          .hass=${this.hass}
          .knx=${this.knx}
          .data=${Object.values(i.direction)}
          .config=${this._directionFilterConfig(this._hasActiveFilters("direction"),this.hass.language)}
          .selectedOptions=${this.controller.filters.direction}
          .pinSelectedItems=${!1}
          .expanded=${"direction"===this.controller.expandedFilter}
          .narrow=${this.narrow}
          .isMobileDevice=${this.isMobileTouchDevice}
          .filterTitle=${this.knx.localize("group_monitor_direction")}
          @selection-changed=${this._handleDirectionFilterChange}
          @expanded-changed=${this._handleDirectionFilterExpanded}
        ></knx-list-filter>

        <!-- Filter for Telegram Type -->
        <knx-list-filter
          slot="filter-pane"
          .hass=${this.hass}
          .knx=${this.knx}
          .data=${Object.values(i.telegramtype)}
          .config=${this._telegramTypeFilterConfig(this._hasActiveFilters("telegramtype"),this.hass.language)}
          .selectedOptions=${this.controller.filters.telegramtype}
          .pinSelectedItems=${!1}
          .expanded=${"telegramtype"===this.controller.expandedFilter}
          .narrow=${this.narrow}
          .isMobileDevice=${this.isMobileTouchDevice}
          .filterTitle=${this.knx.localize("group_monitor_type")}
          @selection-changed=${this._handleTelegramTypeFilterChange}
          @expanded-changed=${this._handleTelegramTypeFilterExpanded}
        ></knx-list-filter>
      </hass-tabs-subpage-data-table>

      <!-- Telegram detail dialog -->
      ${null!==this.controller.selectedTelegramId?this._renderTelegramInfoDialog(this.controller.selectedTelegramId):a.s6}
    `}constructor(...e){super(...e),this.controller=new g.K(this),this._sourceFilterConfig=(0,n.A)(((e,t,i,o)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{fieldName:this.knx.localize("telegram_filter_source_sort_by_primaryText"),filterable:!0,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.id},secondaryField:{fieldName:this.knx.localize("telegram_filter_source_sort_by_secondaryText"),filterable:!0,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.name},badgeField:{fieldName:this.knx.localize("telegram_filter_source_sort_by_badge"),filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`},custom:{totalCount:{fieldName:this.knx.localize("telegram_filter_sort_by_total_count"),filterable:!1,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>e.totalCount.toString()},filteredCount:{fieldName:this.knx.localize("telegram_filter_sort_by_filtered_count"),filterable:!1,sortable:t>0||"filteredCount"===i,sortDisabled:0===t,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>(e.filteredCount||0).toString()}}}))),this._destinationFilterConfig=(0,n.A)(((e,t,i,o)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{fieldName:this.knx.localize("telegram_filter_destination_sort_by_primaryText"),filterable:!0,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.id},secondaryField:{fieldName:this.knx.localize("telegram_filter_destination_sort_by_secondaryText"),filterable:!0,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.name},badgeField:{fieldName:this.knx.localize("telegram_filter_destination_sort_by_badge"),filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`},custom:{totalCount:{fieldName:this.knx.localize("telegram_filter_sort_by_total_count"),filterable:!1,sortable:!0,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>e.totalCount.toString()},filteredCount:{fieldName:this.knx.localize("telegram_filter_sort_by_filtered_count"),filterable:!1,sortable:t>0||"filteredCount"===i,sortDisabled:0===t,sortAscendingText:this.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:this.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>(e.filteredCount||0).toString()}}}))),this._directionFilterConfig=(0,n.A)(((e,t)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{filterable:!1,sortable:!1,mapper:e=>e.id},secondaryField:{filterable:!1,sortable:!1,mapper:e=>e.name},badgeField:{filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`}}))),this._telegramTypeFilterConfig=(0,n.A)(((e,t)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{filterable:!1,sortable:!1,mapper:e=>e.id},secondaryField:{filterable:!1,sortable:!1,mapper:e=>e.name},badgeField:{filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`}}))),this._onFilterSelectionChange=(e,t)=>{this.controller.setFilterFieldValue(e,t,this.route)},this._onFilterExpansionChange=(e,t)=>{this.controller.updateExpandedFilter(e,t)},this._handleSourceFilterChange=e=>{this._onFilterSelectionChange("source",e.detail.value)},this._handleSourceFilterExpanded=e=>{this._onFilterExpansionChange("source",e.detail.expanded)},this._handleDestinationFilterChange=e=>{this._onFilterSelectionChange("destination",e.detail.value)},this._handleDestinationFilterExpanded=e=>{this._onFilterExpansionChange("destination",e.detail.expanded)},this._handleDirectionFilterChange=e=>{this._onFilterSelectionChange("direction",e.detail.value)},this._handleDirectionFilterExpanded=e=>{this._onFilterExpansionChange("direction",e.detail.expanded)},this._handleTelegramTypeFilterChange=e=>{this._onFilterSelectionChange("telegramtype",e.detail.value)},this._handleTelegramTypeFilterExpanded=e=>{this._onFilterExpansionChange("telegramtype",e.detail.expanded)},this._handleSourceFilterToggle=e=>{this.controller.toggleFilterValue("source",e.detail.value,this.route)},this._handleDestinationFilterToggle=e=>{this.controller.toggleFilterValue("destination",e.detail.value,this.route)},this._handleTelegramTypeFilterToggle=e=>{this.controller.toggleFilterValue("telegramtype",e.detail.value,this.route)},this._handleFilterSortChanged=e=>{this.requestUpdate()},this._columns=(0,n.A)(((e,t,i)=>({timestampIso:{showNarrow:!1,filterable:!0,sortable:!0,direction:"desc",title:this.knx.localize("group_monitor_time"),minWidth:"110px",maxWidth:"122px",template:e=>a.qy`
          <knx-table-cell>
            <div class="primary" slot="primary">${(0,u.Zc)(e.timestamp)}</div>
            ${null===e.offset||"timestampIso"!==this.controller.sortColumn&&void 0!==this.controller.sortColumn?a.s6:a.qy`
                  <div class="secondary" slot="secondary">
                    <span>+</span>
                    <span>${this._formatOffsetWithPrecision(e.offset)}</span>
                  </div>
                `}
          </knx-table-cell>
        `},sourceAddress:{showNarrow:!0,filterable:!0,sortable:!0,title:this.knx.localize("group_monitor_source"),flex:2,minWidth:"0",template:e=>a.qy`
          <knx-table-cell-filterable
            .knx=${this.knx}
            .filterValue=${e.sourceAddress}
            .filterDisplayText=${e.sourceAddress}
            .filterActive=${(this.controller.filters.source||[]).includes(e.sourceAddress)}
            .filterDisabled=${this.isMobileTouchDevice}
            @toggle-filter=${this._handleSourceFilterToggle}
          >
            <div class="primary" slot="primary">${e.sourceAddress}</div>
            ${e.sourceText?a.qy`
                  <div class="secondary" slot="secondary" title=${e.sourceText||""}>
                    ${e.sourceText}
                  </div>
                `:a.s6}
          </knx-table-cell-filterable>
        `},sourceText:{hidden:!0,filterable:!0,sortable:!0,title:this.knx.localize("group_monitor_source_name")},sourceName:{showNarrow:!0,hidden:!0,sortable:!1,groupable:!0,filterable:!1,title:this.knx.localize("group_monitor_source")},destinationAddress:{showNarrow:!0,sortable:!0,filterable:!0,title:this.knx.localize("group_monitor_destination"),flex:2,minWidth:"0",template:e=>a.qy`
          <knx-table-cell-filterable
            .knx=${this.knx}
            .filterValue=${e.destinationAddress}
            .filterDisplayText=${e.destinationAddress}
            .filterActive=${(this.controller.filters.destination||[]).includes(e.destinationAddress)}
            .filterDisabled=${this.isMobileTouchDevice}
            @toggle-filter=${this._handleDestinationFilterToggle}
          >
            <div class="primary" slot="primary">${e.destinationAddress}</div>
            ${e.destinationText?a.qy`
                  <div class="secondary" slot="secondary" title=${e.destinationText||""}>
                    ${e.destinationText}
                  </div>
                `:a.s6}
          </knx-table-cell-filterable>
        `},destinationText:{showNarrow:!0,hidden:!0,sortable:!0,filterable:!0,title:this.knx.localize("group_monitor_destination_name")},destinationName:{showNarrow:!0,hidden:!0,sortable:!1,groupable:!0,filterable:!1,title:this.knx.localize("group_monitor_destination")},type:{showNarrow:!1,title:this.knx.localize("group_monitor_type"),filterable:!0,sortable:!0,groupable:!0,minWidth:"155px",maxWidth:"155px",template:e=>a.qy`
          <knx-table-cell-filterable
            .knx=${this.knx}
            .filterValue=${e.type}
            .filterDisplayText=${e.type}
            .filterActive=${(this.controller.filters.telegramtype||[]).includes(e.type)}
            .filterDisabled=${this.isMobileTouchDevice}
            @toggle-filter=${this._handleTelegramTypeFilterToggle}
          >
            <div class="primary" slot="primary" title=${e.type}>${e.type}</div>
            <div
              class="secondary"
              slot="secondary"
              style="color: ${"Outgoing"===e.direction?"var(--knx-blue)":"var(--knx-green)"}"
            >
              ${e.direction}
            </div>
          </knx-table-cell-filterable>
        `},direction:{hidden:!0,title:this.knx.localize("group_monitor_direction"),filterable:!0,groupable:!0},payload:{showNarrow:!1,hidden:e&&t,title:this.knx.localize("group_monitor_payload"),filterable:!0,sortable:!0,type:"numeric",minWidth:"105px",maxWidth:"105px",template:e=>e.payload?a.qy`
            <code
              style="
                display: inline-block;
                box-sizing: border-box;
                max-width: 100%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-size: 0.9em;
                background: var(--secondary-background-color);
                padding: 2px 4px;
                border-radius: 4px;
              "
              title=${e.payload}
            >
              ${e.payload}
            </code>
          `:a.s6},value:{showNarrow:!0,hidden:!t,title:this.knx.localize("group_monitor_value"),filterable:!0,sortable:!0,flex:1,minWidth:"0",template:e=>{const t=e.value;return t?a.qy`
            <knx-table-cell>
              <span
                class="primary"
                slot="primary"
                style="font-weight: 500; color: var(--primary-color);"
                title=${t}
              >
                ${t}
              </span>
            </knx-table-cell>
          `:a.s6}}})))}}(0,r.__decorate)([(0,p.MZ)({type:Object})],x.prototype,"hass",void 0),(0,r.__decorate)([(0,p.MZ)({attribute:!1})],x.prototype,"knx",void 0),(0,r.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],x.prototype,"narrow",void 0),(0,r.__decorate)([(0,p.MZ)({type:Object})],x.prototype,"route",void 0),(0,r.__decorate)([(0,p.MZ)({type:Array,reflect:!1})],x.prototype,"tabs",void 0),(0,r.__decorate)([(0,p.P)('knx-list-filter[data-filter="source"]')],x.prototype,"sourceFilter",void 0),(0,r.__decorate)([(0,p.P)('knx-list-filter[data-filter="destination"]')],x.prototype,"destinationFilter",void 0),x=(0,r.__decorate)([(0,p.EM)("knx-group-monitor")],x),o()}catch(_){o(_)}}))},25474:function(e,t,i){i.d(t,{CY:()=>s,HF:()=>n,RL:()=>m,Zc:()=>a,e4:()=>r,u_:()=>g});var o=i(53289);const r={payload:e=>null==e.payload?"":Array.isArray(e.payload)?e.payload.reduce(((e,t)=>e+t.toString(16).padStart(2,"0")),"0x"):e.payload.toString(),valueWithUnit:e=>null==e.value?"":"number"==typeof e.value||"boolean"==typeof e.value||"string"==typeof e.value?e.value.toString()+(e.unit?" "+e.unit:""):(0,o.Bh)(e.value),timeWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString(["en-US"],{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dateWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dptNumber:e=>null==e.dpt_main?"":null==e.dpt_sub?e.dpt_main.toString():e.dpt_main.toString()+"."+e.dpt_sub.toString().padStart(3,"0"),dptNameNumber:e=>{const t=r.dptNumber(e);return null==e.dpt_name?`DPT ${t}`:t?`DPT ${t} ${e.dpt_name}`:e.dpt_name}},a=e=>e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),n=e=>e.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),s=e=>{const t=new Date(e),i=e.match(/\.(\d{6})/),o=i?i[1]:"000000";return t.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+t.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit"})+"."+o},l=1e3,d=1e3,c=60*d,h=60*c,p=2,u=3;function g(e){const t=e.indexOf(".");if(-1===t)return 1e3*Date.parse(e);let i=e.indexOf("Z",t);-1===i&&(i=e.indexOf("+",t),-1===i&&(i=e.indexOf("-",t))),-1===i&&(i=e.length);const o=e.slice(0,t)+e.slice(i),r=Date.parse(o);let a=e.slice(t+1,i);return a.length<6?a=a.padEnd(6,"0"):a.length>6&&(a=a.slice(0,6)),1e3*r+Number(a)}function m(e,t="milliseconds"){if(null==e)return"—";const i=e<0?"-":"",o=Math.abs(e),r="milliseconds"===t?Math.round(o/l):Math.floor(o/l),a="microseconds"===t?o%l:0,n=Math.floor(r/h),s=Math.floor(r%h/c),g=Math.floor(r%c/d),m=r%d,_=e=>e.toString().padStart(p,"0"),f=e=>e.toString().padStart(u,"0"),b="microseconds"===t?`.${f(m)}${f(a)}`:`.${f(m)}`,v=`${_(s)}:${_(g)}`;return`${i}${n>0?`${_(n)}:${v}`:v}${b}`}},25625:function(e,t,i){i.d(t,{H:()=>n});var o=i(9160),r=i(73420),a=i(83504);function n(e,t){const i=()=>(0,r.w)(t?.in,NaN),n=t?.additionalDigits??2,m=function(e){const t={},i=e.split(s.dateTimeDelimiter);let o;if(i.length>2)return t;/:/.test(i[0])?o=i[0]:(t.date=i[0],o=i[1],s.timeZoneDelimiter.test(t.date)&&(t.date=e.split(s.timeZoneDelimiter)[0],o=e.substr(t.date.length,e.length)));if(o){const e=s.timezone.exec(o);e?(t.time=o.replace(e[1],""),t.timezone=e[1]):t.time=o}return t}(e);let _;if(m.date){const e=function(e,t){const i=new RegExp("^(?:(\\d{4}|[+-]\\d{"+(4+t)+"})|(\\d{2}|[+-]\\d{"+(2+t)+"})$)"),o=e.match(i);if(!o)return{year:NaN,restDateString:""};const r=o[1]?parseInt(o[1]):null,a=o[2]?parseInt(o[2]):null;return{year:null===a?r:100*a,restDateString:e.slice((o[1]||o[2]).length)}}(m.date,n);_=function(e,t){if(null===t)return new Date(NaN);const i=e.match(l);if(!i)return new Date(NaN);const o=!!i[4],r=h(i[1]),a=h(i[2])-1,n=h(i[3]),s=h(i[4]),d=h(i[5])-1;if(o)return function(e,t,i){return t>=1&&t<=53&&i>=0&&i<=6}(0,s,d)?function(e,t,i){const o=new Date(0);o.setUTCFullYear(e,0,4);const r=o.getUTCDay()||7,a=7*(t-1)+i+1-r;return o.setUTCDate(o.getUTCDate()+a),o}(t,s,d):new Date(NaN);{const e=new Date(0);return function(e,t,i){return t>=0&&t<=11&&i>=1&&i<=(u[t]||(g(e)?29:28))}(t,a,n)&&function(e,t){return t>=1&&t<=(g(e)?366:365)}(t,r)?(e.setUTCFullYear(t,a,Math.max(r,n)),e):new Date(NaN)}}(e.restDateString,e.year)}if(!_||isNaN(+_))return i();const f=+_;let b,v=0;if(m.time&&(v=function(e){const t=e.match(d);if(!t)return NaN;const i=p(t[1]),r=p(t[2]),a=p(t[3]);if(!function(e,t,i){if(24===e)return 0===t&&0===i;return i>=0&&i<60&&t>=0&&t<60&&e>=0&&e<25}(i,r,a))return NaN;return i*o.s0+r*o.Cg+1e3*a}(m.time),isNaN(v)))return i();if(!m.timezone){const e=new Date(f+v),i=(0,a.a)(0,t?.in);return i.setFullYear(e.getUTCFullYear(),e.getUTCMonth(),e.getUTCDate()),i.setHours(e.getUTCHours(),e.getUTCMinutes(),e.getUTCSeconds(),e.getUTCMilliseconds()),i}return b=function(e){if("Z"===e)return 0;const t=e.match(c);if(!t)return 0;const i="+"===t[1]?-1:1,r=parseInt(t[2]),a=t[3]&&parseInt(t[3])||0;if(!function(e,t){return t>=0&&t<=59}(0,a))return NaN;return i*(r*o.s0+a*o.Cg)}(m.timezone),isNaN(b)?i():(0,a.a)(f+v+b,t?.in)}const s={dateTimeDelimiter:/[T ]/,timeZoneDelimiter:/[Z ]/i,timezone:/([Z+-].*)$/},l=/^-?(?:(\d{3})|(\d{2})(?:-?(\d{2}))?|W(\d{2})(?:-?(\d{1}))?|)$/,d=/^(\d{2}(?:[.,]\d*)?)(?::?(\d{2}(?:[.,]\d*)?))?(?::?(\d{2}(?:[.,]\d*)?))?$/,c=/^([+-])(\d{2})(?::?(\d{2}))?$/;function h(e){return e?parseInt(e):1}function p(e){return e&&parseFloat(e.replace(",","."))||0}const u=[31,null,31,30,31,30,31,31,30,31,30,31];function g(e){return e%400==0||e%4==0&&e%100!=0}},58673:function(e,t,i){i.d(t,{a:()=>n});var o=i(5055),r=i(42017);const a={},n=(0,r.u$)(class extends r.WL{render(e,t){return t()}update(e,[t,i]){if(Array.isArray(t)){if(Array.isArray(this.ot)&&this.ot.length===t.length&&t.every(((e,t)=>e===this.ot[t])))return o.c0}else if(this.ot===t)return o.c0;return this.ot=Array.isArray(t)?Array.from(t):t,this.render(t,i)}constructor(){super(...arguments),this.ot=a}})}};
//# sourceMappingURL=5643.189e8dc038b941ba.js.map