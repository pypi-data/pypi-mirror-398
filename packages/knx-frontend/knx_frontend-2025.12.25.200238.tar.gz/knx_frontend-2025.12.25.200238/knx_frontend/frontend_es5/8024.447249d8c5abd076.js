"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8024"],{10253:function(e,t,i){i.a(e,(async function(e,o){try{i.d(t,{P:function(){return d}});i(74423),i(25276);var r=i(22),n=i(58109),a=i(81793),l=i(44740),s=e([r]);r=(s.then?(await s)():s)[0];var d=e=>e.first_weekday===a.zt.language?"weekInfo"in Intl.Locale.prototype?new Intl.Locale(e.language).weekInfo.firstDay%7:(0,n.S)(e.language)%7:l.Z.includes(e.first_weekday)?l.Z.indexOf(e.first_weekday):1;o()}catch(c){o(c)}}))},77646:function(e,t,i){i.a(e,(async function(e,o){try{i.d(t,{K:function(){return d}});var r=i(22),n=i(22786),a=i(97518),l=e([r,a]);[r,a]=l.then?(await l)():l;var s=(0,n.A)((e=>new Intl.RelativeTimeFormat(e.language,{numeric:"auto"}))),d=function(e,t,i){var o=!(arguments.length>3&&void 0!==arguments[3])||arguments[3],r=(0,a.x)(e,i,t);return o?s(t).format(r.value,r.unit):Intl.NumberFormat(t.language,{style:"unit",unit:r.unit,unitDisplay:"long"}).format(Math.abs(r.value))};o()}catch(c){o(c)}}))},44740:function(e,t,i){i.d(t,{Z:function(){return o}});var o=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"]},74522:function(e,t,i){i.d(t,{Z:function(){return o}});i(34782);var o=e=>e.charAt(0).toUpperCase()+e.slice(1)},93777:function(e,t,i){i.d(t,{Y:function(){return o}});i(26099),i(84864),i(57465),i(27495),i(38781),i(25440);var o=function(e){var t,i=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"_",o="àáâäæãåāăąабçćčđďдèéêëēėęěеёэфğǵгḧхîïíīįìıİийкłлḿмñńǹňнôöòóœøōõőоṕпŕřрßśšşșсťțтûüùúūǘůűųувẃẍÿýыžźżз·",r=`aaaaaaaaaaabcccdddeeeeeeeeeeefggghhiiiiiiiiijkllmmnnnnnoooooooooopprrrsssssstttuuuuuuuuuuvwxyyyzzzz${i}`,n=new RegExp(o.split("").join("|"),"g"),a={"ж":"zh","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ю":"iu","я":"ia"};return""===e?t="":""===(t=e.toString().toLowerCase().replace(n,(e=>r.charAt(o.indexOf(e)))).replace(/[а-я]/g,(e=>a[e]||"")).replace(/(\d),(?=\d)/g,"$1").replace(/[^a-z0-9]+/g,i).replace(new RegExp(`(${i})\\1+`,"g"),"$1").replace(new RegExp(`^${i}+`),"").replace(new RegExp(`${i}+$`),""))&&(t="unknown"),t}},97518:function(e,t,i){i.a(e,(async function(e,o){try{i.d(t,{x:function(){return g}});var r=i(6946),n=i(52640),a=i(56232),l=i(10253),s=e([l]);l=(s.then?(await s)():s)[0];var d=1e3,c=60,u=60*c;function g(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:Date.now(),i=arguments.length>2?arguments[2]:void 0,o=arguments.length>3&&void 0!==arguments[3]?arguments[3]:{},s=Object.assign(Object.assign({},h),o||{}),p=(+e-+t)/d;if(Math.abs(p)<s.second)return{value:Math.round(p),unit:"second"};var g=p/c;if(Math.abs(g)<s.minute)return{value:Math.round(g),unit:"minute"};var f=p/u;if(Math.abs(f)<s.hour)return{value:Math.round(f),unit:"hour"};var v=new Date(e),m=new Date(t);v.setHours(0,0,0,0),m.setHours(0,0,0,0);var _=(0,r.c)(v,m);if(0===_)return{value:Math.round(f),unit:"hour"};if(Math.abs(_)<s.day)return{value:_,unit:"day"};var b=(0,l.P)(i),y=(0,n.k)(v,{weekStartsOn:b}),x=(0,n.k)(m,{weekStartsOn:b}),k=(0,a.I)(y,x);if(0===k)return{value:_,unit:"day"};if(Math.abs(k)<s.week)return{value:k,unit:"week"};var w=v.getFullYear()-m.getFullYear(),$=12*w+v.getMonth()-m.getMonth();return 0===$?{value:k,unit:"week"}:Math.abs($)<s.month||0===w?{value:$,unit:"month"}:{value:Math.round(w),unit:"year"}}var h={second:59,minute:59,hour:22,day:5,week:4,month:11};o()}catch(p){o(p)}}))},89473:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(44734),r=i(56038),n=i(69683),a=i(6454),l=(i(28706),i(62826)),s=i(88496),d=i(96196),c=i(77845),u=e([s]);s=(u.then?(await u)():u)[0];var h,p=e=>e,g=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,n.A)(this,t,[].concat(r))).variant="brand",e}return(0,a.A)(t,e),(0,r.A)(t,null,[{key:"styles",get:function(){return[s.A.styles,(0,d.AH)(h||(h=p`
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
      `))]}}])}(s.A);g=(0,l.__decorate)([(0,c.EM)("ha-button")],g),t()}catch(f){t(f)}}))},95637:function(e,t,i){i.d(t,{l:function(){return _}});var o,r,n,a=i(44734),l=i(56038),s=i(69683),d=i(6454),c=i(25460),u=(i(78170),i(28706),i(62826)),h=i(30728),p=i(47705),g=i(96196),f=i(77845),v=(i(41742),i(60733),e=>e),m=["button","ha-list-item"],_=(e,t)=>{var i;return(0,g.qy)(o||(o=v`
  <div class="header_title">
    <ha-icon-button
      .label=${0}
      .path=${0}
      dialogAction="close"
      class="header_button"
    ></ha-icon-button>
    <span>${0}</span>
  </div>
`),null!==(i=null==e?void 0:e.localize("ui.common.close"))&&void 0!==i?i:"Close","M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",t)},b=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(o)))._onScroll=()=>{e._updateScrolledAttribute()},e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"scrollToPos",value:function(e,t){var i;null===(i=this.contentElement)||void 0===i||i.scrollTo(e,t)}},{key:"renderHeading",value:function(){return(0,g.qy)(r||(r=v`<slot name="heading"> ${0} </slot>`),(0,c.A)(t,"renderHeading",this,3)([]))}},{key:"firstUpdated",value:function(){var e;(0,c.A)(t,"firstUpdated",this,3)([]),this.suppressDefaultPressSelector=[this.suppressDefaultPressSelector,m].join(", "),this._updateScrolledAttribute(),null===(e=this.contentElement)||void 0===e||e.addEventListener("scroll",this._onScroll,{passive:!0})}},{key:"disconnectedCallback",value:function(){(0,c.A)(t,"disconnectedCallback",this,3)([]),this.contentElement.removeEventListener("scroll",this._onScroll)}},{key:"_updateScrolledAttribute",value:function(){this.contentElement&&this.toggleAttribute("scrolled",0!==this.contentElement.scrollTop)}}])}(h.u);b.styles=[p.R,(0,g.AH)(n||(n=v`
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
    `))],b=(0,u.__decorate)([(0,f.EM)("ha-dialog")],b)},35150:function(e,t,i){i.r(t),i.d(t,{HaIconButtonToggle:function(){return u}});var o,r=i(56038),n=i(44734),a=i(69683),l=i(6454),s=(i(28706),i(62826)),d=i(96196),c=i(77845),u=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,a.A)(this,t,[].concat(o))).selected=!1,e}return(0,l.A)(t,e),(0,r.A)(t)}(i(60733).HaIconButton);u.styles=(0,d.AH)(o||(o=(e=>e)`
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
  `)),(0,s.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0})],u.prototype,"selected",void 0),u=(0,s.__decorate)([(0,c.EM)("ha-icon-button-toggle")],u)},18043:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(44734),r=i(56038),n=i(69683),a=i(6454),l=i(25460),s=(i(28706),i(62826)),d=i(25625),c=i(96196),u=i(77845),h=i(77646),p=i(74522),g=e([h]);h=(g.then?(await g)():g)[0];var f=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,n.A)(this,t,[].concat(r))).capitalize=!1,e}return(0,a.A)(t,e),(0,r.A)(t,[{key:"disconnectedCallback",value:function(){(0,l.A)(t,"disconnectedCallback",this,3)([]),this._clearInterval()}},{key:"connectedCallback",value:function(){(0,l.A)(t,"connectedCallback",this,3)([]),this.datetime&&this._startInterval()}},{key:"createRenderRoot",value:function(){return this}},{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),this._updateRelative()}},{key:"update",value:function(e){(0,l.A)(t,"update",this,3)([e]),this._updateRelative()}},{key:"_clearInterval",value:function(){this._interval&&(window.clearInterval(this._interval),this._interval=void 0)}},{key:"_startInterval",value:function(){this._clearInterval(),this._interval=window.setInterval((()=>this._updateRelative()),6e4)}},{key:"_updateRelative",value:function(){if(this.datetime){var e="string"==typeof this.datetime?(0,d.H)(this.datetime):this.datetime,t=(0,h.K)(e,this.hass.locale);this.innerHTML=this.capitalize?(0,p.Z)(t):t}else this.innerHTML=this.hass.localize("ui.components.relative_time.never")}}])}(c.mN);(0,s.__decorate)([(0,u.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],f.prototype,"datetime",void 0),(0,s.__decorate)([(0,u.MZ)({type:Boolean})],f.prototype,"capitalize",void 0),f=(0,s.__decorate)([(0,u.EM)("ha-relative-time")],f),t()}catch(v){t(v)}}))},21912:function(e,t,i){i.d(t,{M:function(){return o}});i(27495),i(90906);var o=/(?:iphone|android|ipad)/i.test(navigator.userAgent)},80111:function(e,t,i){i.d(t,{C:function(){return o}});var o="ontouchstart"in window||navigator.maxTouchPoints>0||navigator.msMaxTouchPoints>0},7791:function(e,t,i){var o,r,n,a=i(94741),l=i(44734),s=i(56038),d=i(69683),c=i(6454),u=(i(28706),i(62826)),h=i(96196),p=i(77845),g=(i(60733),i(41508)),f=e=>e,v=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).filterActive=!1,e.filterDisabled=!1,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,h.qy)(o||(o=f`
      <div class="container">
        <div class="content-wrapper">
          <slot name="primary"></slot>
          <slot name="secondary"></slot>
        </div>
        <!-- Filter Button - conditionally rendered based on filterValue and filterDisabled -->
        ${0}
      </div>
    `),this.filterValue&&!this.filterDisabled?(0,h.qy)(r||(r=f`
              <div class="filter-button ${0}">
                <ha-icon-button
                  .path=${0}
                  @click=${0}
                  .title=${0}
                >
                </ha-icon-button>
              </div>
            `),this.filterActive?"filter-active":"",this.filterActive?"M21 8H3V6H21V8M13.81 16H10V18H13.09C13.21 17.28 13.46 16.61 13.81 16M18 11H6V13H18V11M21.12 15.46L19 17.59L16.88 15.46L15.47 16.88L17.59 19L15.47 21.12L16.88 22.54L19 20.41L21.12 22.54L22.54 21.12L20.41 19L22.54 16.88L21.12 15.46Z":"M6,13H18V11H6M3,6V8H21V6M10,18H14V16H10V18Z",this._handleFilterClick,this.knx.localize(this.filterActive?"knx_table_cell_filterable_filter_remove_tooltip":"knx_table_cell_filterable_filter_set_tooltip",{value:this.filterDisplayText||this.filterValue})):h.s6)}},{key:"_handleFilterClick",value:function(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("toggle-filter",{bubbles:!0,composed:!0,detail:{value:this.filterValue,active:!this.filterActive}})),this.filterActive=!this.filterActive}}])}(g._);v.styles=[].concat((0,a.A)(g._.styles),[(0,h.AH)(n||(n=f`
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
    `))]),(0,u.__decorate)([(0,p.MZ)({type:Object})],v.prototype,"knx",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"filterValue",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"filterDisplayText",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"filterActive",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],v.prototype,"filterDisabled",void 0),v=(0,u.__decorate)([(0,p.EM)("knx-table-cell-filterable")],v)},41508:function(e,t,i){i.d(t,{_:function(){return p}});var o,r,n=i(44734),a=i(56038),l=i(69683),s=i(6454),d=i(62826),c=i(96196),u=i(77845),h=e=>e,p=function(e){function t(){return(0,n.A)(this,t),(0,l.A)(this,t,arguments)}return(0,s.A)(t,e),(0,a.A)(t,[{key:"render",value:function(){return(0,c.qy)(o||(o=h`
      <div class="container">
        <div class="content-wrapper">
          <slot name="primary"></slot>
          <slot name="secondary"></slot>
        </div>
      </div>
    `))}}])}(c.WF);p.styles=[(0,c.AH)(r||(r=h`
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
    `))],p=(0,d.__decorate)([(0,u.EM)("knx-table-cell")],p)},1002:function(e,t,i){var o,r=i(94741),n=i(78261),a=i(31432),l=i(44734),s=i(56038),d=i(69683),c=i(6454),u=i(25460),h=(i(16280),i(28706),i(2008),i(74423),i(62062),i(44114),i(26910),i(18111),i(22489),i(7588),i(61701),i(33110),i(5506),i(26099),i(16034),i(38781),i(23500),i(62826)),p=i(96196),g=i(77845),f=i(94333),v=i(58673),m=i(32288),_=i(4937),b=(i(70524),i(34811)),y=(i(60733),i(35150),i(60961),i(96270),i(39396)),x=i(92542),k="asc",w=new Intl.Collator(void 0,{numeric:!0,sensitivity:"base"}),$=function(e){function t(){return(0,l.A)(this,t),(0,d.A)(this,t,arguments)}return(0,c.A)(t,e),(0,s.A)(t)}(b.p);$.styles=(0,p.AH)(o||(o=(e=>e)`
    /* Inherit base styles */
    ${0}

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
  `),b.p.styles),$=(0,h.__decorate)([(0,g.EM)("flex-content-expansion-panel")],$);i(7153),i(1554),i(56565);var A,C,F,T,S=e=>e,D=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).criterion="idField",e.displayName="",e.defaultDirection=H.DEFAULT_DIRECTION,e.direction=H.ASC,e.active=!1,e.ascendingIcon=t.DEFAULT_ASC_ICON,e.descendingIcon=t.DEFAULT_DESC_ICON,e.isMobileDevice=!1,e.disabled=!1,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"_ascendingText",get:function(){var e,t,i;return null!==(e=null!==(t=this.ascendingText)&&void 0!==t?t:null===(i=this.knx)||void 0===i?void 0:i.localize("knx_sort_menu_item_ascending"))&&void 0!==e?e:""}},{key:"_descendingText",get:function(){var e,t,i;return null!==(e=null!==(t=this.descendingText)&&void 0!==t?t:null===(i=this.knx)||void 0===i?void 0:i.localize("knx_sort_menu_item_descending"))&&void 0!==e?e:""}},{key:"render",value:function(){return(0,p.qy)(A||(A=S`
      <ha-list-item
        class="sort-row ${0} ${0}"
        @click=${0}
      >
        <div class="container">
          <div class="sort-field-name" title=${0} aria-label=${0}>
            ${0}
          </div>
          <div class="sort-buttons">
            ${0}
          </div>
        </div>
      </ha-list-item>
    `),this.active?"active":"",this.disabled?"disabled":"",this.disabled?p.s6:this._handleItemClick,this.displayName,this.displayName,this.displayName,this.isMobileDevice?this._renderMobileButtons():this._renderDesktopButtons())}},{key:"_renderMobileButtons",value:function(){if(!this.active)return p.s6;var e=this.direction===H.DESC;return(0,p.qy)(C||(C=S`
      <ha-icon-button
        class="active"
        .path=${0}
        .label=${0}
        .title=${0}
        .disabled=${0}
        @click=${0}
      ></ha-icon-button>
    `),e?this.descendingIcon:this.ascendingIcon,e?this._descendingText:this._ascendingText,e?this._descendingText:this._ascendingText,this.disabled,this.disabled?p.s6:this._handleMobileButtonClick)}},{key:"_renderDesktopButtons",value:function(){return(0,p.qy)(F||(F=S`
      <ha-icon-button
        class=${0}
        .path=${0}
        .label=${0}
        .title=${0}
        .disabled=${0}
        @click=${0}
      ></ha-icon-button>
      <ha-icon-button
        class=${0}
        .path=${0}
        .label=${0}
        .title=${0}
        .disabled=${0}
        @click=${0}
      ></ha-icon-button>
    `),this.active&&this.direction===H.DESC?"active":"",this.descendingIcon,this._descendingText,this._descendingText,this.disabled,this.disabled?p.s6:this._handleDescendingClick,this.active&&this.direction===H.ASC?"active":"",this.ascendingIcon,this._ascendingText,this._ascendingText,this.disabled,this.disabled?p.s6:this._handleAscendingClick)}},{key:"_handleDescendingClick",value:function(e){e.stopPropagation(),(0,x.r)(this,"sort-option-selected",{criterion:this.criterion,direction:H.DESC})}},{key:"_handleAscendingClick",value:function(e){e.stopPropagation(),(0,x.r)(this,"sort-option-selected",{criterion:this.criterion,direction:H.ASC})}},{key:"_handleItemClick",value:function(){var e=this.active?this.direction===H.ASC?H.DESC:H.ASC:this.defaultDirection;(0,x.r)(this,"sort-option-selected",{criterion:this.criterion,direction:e})}},{key:"_handleMobileButtonClick",value:function(e){e.stopPropagation();var t=this.direction===H.ASC?H.DESC:H.ASC;(0,x.r)(this,"sort-option-selected",{criterion:this.criterion,direction:t})}}])}(p.WF);D.DEFAULT_ASC_ICON="M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",D.DEFAULT_DESC_ICON="M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z",D.styles=(0,p.AH)(T||(T=S`
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
  `)),(0,h.__decorate)([(0,g.MZ)({type:Object})],D.prototype,"knx",void 0),(0,h.__decorate)([(0,g.MZ)({type:String})],D.prototype,"criterion",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"display-name"})],D.prototype,"displayName",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"default-direction"})],D.prototype,"defaultDirection",void 0),(0,h.__decorate)([(0,g.MZ)({type:String})],D.prototype,"direction",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean})],D.prototype,"active",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"ascending-text"})],D.prototype,"ascendingText",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"descending-text"})],D.prototype,"descendingText",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"ascending-icon"})],D.prototype,"ascendingIcon",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"descending-icon"})],D.prototype,"descendingIcon",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean,attribute:"is-mobile-device"})],D.prototype,"isMobileDevice",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean})],D.prototype,"disabled",void 0),D=(0,h.__decorate)([(0,g.EM)("knx-sort-menu-item")],D);var M,z,L=e=>e,H=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).sortCriterion="",e.sortDirection=t.DEFAULT_DIRECTION,e.isMobileDevice=!1,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"updated",value:function(e){(0,u.A)(t,"updated",this,3)([e]),(e.has("sortCriterion")||e.has("sortDirection")||e.has("isMobileDevice"))&&this._updateMenuItems()}},{key:"_updateMenuItems",value:function(){this._sortMenuItems&&this._sortMenuItems.forEach((e=>{e.active=e.criterion===this.sortCriterion,e.direction=e.criterion===this.sortCriterion?this.sortDirection:e.defaultDirection,e.knx=this.knx,e.isMobileDevice=this.isMobileDevice}))}},{key:"render",value:function(){var e,t;return(0,p.qy)(M||(M=L`
      <div class="menu-container">
        <ha-menu
          .corner=${0}
          .fixed=${0}
          @opened=${0}
          @closed=${0}
        >
          <slot name="header">
            <div class="header">
              <div class="title">
                <!-- Slot for custom title -->
                <slot name="title">${0}</slot>
              </div>
              <div class="toolbar">
                <!-- Slot for adding custom buttons to the header -->
                <slot name="toolbar"></slot>
              </div>
            </div>
            <li divider></li>
          </slot>

          <!-- Menu items will be slotted here -->
          <slot @sort-option-selected=${0}></slot>
        </ha-menu>
      </div>
    `),"BOTTOM_START",!0,this._handleMenuOpened,this._handleMenuClosed,null!==(e=null===(t=this.knx)||void 0===t?void 0:t.localize("knx_sort_menu_sort_by"))&&void 0!==e?e:"",this._handleSortOptionSelected)}},{key:"openMenu",value:function(e){this._menu&&(this._menu.anchor=e,this._menu.show())}},{key:"closeMenu",value:function(){this._menu&&this._menu.close()}},{key:"_updateSorting",value:function(e,t){e===this.sortCriterion&&t===this.sortDirection||(this.sortCriterion=e,this.sortDirection=t,(0,x.r)(this,"sort-changed",{criterion:e,direction:t}))}},{key:"_handleMenuOpened",value:function(){this._updateMenuItems()}},{key:"_handleMenuClosed",value:function(){}},{key:"_handleSortOptionSelected",value:function(e){var t=e.detail,i=t.criterion,o=t.direction;this._updateSorting(i,o),this.closeMenu()}}])}(p.WF);H.ASC="asc",H.DESC="desc",H.DEFAULT_DIRECTION=H.ASC,H.styles=(0,p.AH)(z||(z=L`
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
  `)),(0,h.__decorate)([(0,g.MZ)({type:Object})],H.prototype,"knx",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"sort-criterion"})],H.prototype,"sortCriterion",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"sort-direction"})],H.prototype,"sortDirection",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean,attribute:"is-mobile-device"})],H.prototype,"isMobileDevice",void 0),(0,h.__decorate)([(0,g.P)("ha-menu")],H.prototype,"_menu",void 0),(0,h.__decorate)([(0,g.KN)({selector:"knx-sort-menu-item"})],H.prototype,"_sortMenuItems",void 0),H=(0,h.__decorate)([(0,g.EM)("knx-sort-menu")],H);i(2892);var I,O,E=e=>e,V=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).height=1,e.maxHeight=50,e.minHeight=1,e.animationDuration=150,e.customClass="",e._isTransitioning=!1,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"setHeight",value:function(e){var t=!(arguments.length>1&&void 0!==arguments[1])||arguments[1],i=Math.max(this.minHeight,Math.min(this.maxHeight,e));t?(this._isTransitioning=!0,this.height=i,setTimeout((()=>{this._isTransitioning=!1}),this.animationDuration)):this.height=i}},{key:"expand",value:function(){this.setHeight(this.maxHeight)}},{key:"collapse",value:function(){this.setHeight(this.minHeight)}},{key:"toggle",value:function(){var e=this.minHeight+.5*(this.maxHeight-this.minHeight);this.height<=e?this.expand():this.collapse()}},{key:"expansionRatio",get:function(){return(this.height-this.minHeight)/(this.maxHeight-this.minHeight)}},{key:"render",value:function(){return(0,p.qy)(I||(I=E`
      <div
        class="separator-container ${0}"
        style="
          height: ${0}px;
          transition: ${0};
        "
      >
        <div class="content">
          <slot></slot>
        </div>
      </div>
    `),this.customClass,this.height,this._isTransitioning?`height ${this.animationDuration}ms ease-in-out`:"none")}}])}(p.WF);V.styles=(0,p.AH)(O||(O=E`
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
  `)),(0,h.__decorate)([(0,g.MZ)({type:Number,reflect:!0})],V.prototype,"height",void 0),(0,h.__decorate)([(0,g.MZ)({type:Number,attribute:"max-height"})],V.prototype,"maxHeight",void 0),(0,h.__decorate)([(0,g.MZ)({type:Number,attribute:"min-height"})],V.prototype,"minHeight",void 0),(0,h.__decorate)([(0,g.MZ)({type:Number,attribute:"animation-duration"})],V.prototype,"animationDuration",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"custom-class"})],V.prototype,"customClass",void 0),(0,h.__decorate)([(0,g.wk)()],V.prototype,"_isTransitioning",void 0),V=(0,h.__decorate)([(0,g.EM)("knx-separator")],V);var Z,q,j,N,P,R,B,U,W,K,G,Q,Y,J,X,ee,te,ie,oe,re,ne=e=>e,ae=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).data=[],e.expanded=!1,e.narrow=!1,e.pinSelectedItems=!0,e.filterQuery="",e.sortCriterion="primaryField",e.sortDirection="asc",e.isMobileDevice=!1,e._separatorMaxHeight=28,e._separatorMinHeight=2,e._separatorAnimationDuration=150,e._separatorScrollZone=28,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"_computeFilterSortedOptions",value:function(){var e=this._computeFilteredOptions(),t=this._getComparator();return this._sortOptions(e,t,this.sortDirection)}},{key:"_computeFilterSortedOptionsWithSeparator",value:function(){var e,t=this._computeFilteredOptions(),i=this._getComparator(),o=[],r=[],n=(0,a.A)(t);try{for(n.s();!(e=n.n()).done;){var l=e.value;l.selected?o.push(l):r.push(l)}}catch(s){n.e(s)}finally{n.f()}return{selected:this._sortOptions(o,i,this.sortDirection),unselected:this._sortOptions(r,i,this.sortDirection)}}},{key:"_computeFilteredOptions",value:function(){var e=this.data,t=this.config,i=t.idField,o=t.primaryField,r=t.secondaryField,a=t.badgeField,l=t.custom,s=this.selectedOptions,d=void 0===s?[]:s,c=e.map((e=>{var t=i.mapper(e),s=o.mapper(e);if(!t||!s)throw new Error("Missing id or primary field on item: "+JSON.stringify(e));var c={idField:t,primaryField:s,secondaryField:r.mapper(e),badgeField:a.mapper(e),selected:d.includes(t)};return l&&Object.entries(l).forEach((t=>{var i=(0,n.A)(t,2),o=i[0],r=i[1];c[o]=r.mapper(e)})),c}));return this._applyFilterToOptions(c)}},{key:"_getComparator",value:function(){var e=this._getFieldConfig(this.sortCriterion);return null!=e&&e.comparator?e.comparator:this._generateComparator(this.sortCriterion)}},{key:"_getFieldConfig",value:function(e){var t,i=this.config;return e in i&&"custom"!==e?i[e]:null===(t=i.custom)||void 0===t?void 0:t[e]}},{key:"_generateComparator",value:function(e){return(t,i)=>{var o=this._compareByField(t,i,e);return 0!==o?o:this._lazyFallbackComparison(t,i,e)}}},{key:"_lazyFallbackComparison",value:function(e,t,i){var o,r=this._getFallbackFields(i),n=(0,a.A)(r);try{for(n.s();!(o=n.n()).done;){var l=o.value,s=this._compareByField(e,t,l);if(0!==s)return s}}catch(d){n.e(d)}finally{n.f()}return this._compareByField(e,t,"idField")}},{key:"_getFallbackFields",value:function(e){return{idField:[],primaryField:["secondaryField","badgeField"],secondaryField:["primaryField","badgeField"],badgeField:["primaryField","secondaryField"]}[e]||["primaryField"]}},{key:"_compareByField",value:function(e,t,i){var o,r,n=e[i],a=t[i],l="string"==typeof n?n:null!==(o=null==n?void 0:n.toString())&&void 0!==o?o:"",s="string"==typeof a?a:null!==(r=null==a?void 0:a.toString())&&void 0!==r?r:"";return w.compare(l,s)}},{key:"firstUpdated",value:function(){this._setupSeparatorScrollHandler()}},{key:"updated",value:function(e){(e.has("expanded")||e.has("pinSelectedItems"))&&requestAnimationFrame((()=>{this._setupSeparatorScrollHandler(),(e.has("expanded")&&this.expanded||e.has("pinSelectedItems")&&this.pinSelectedItems)&&requestAnimationFrame((()=>{this._handleSeparatorScroll()}))}))}},{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._cleanupSeparatorScrollHandler()}},{key:"_setupSeparatorScrollHandler",value:function(){this._cleanupSeparatorScrollHandler(),this._boundScrollHandler||(this._boundScrollHandler=this._handleSeparatorScroll.bind(this)),this.pinSelectedItems&&this._optionsListContainer&&this._optionsListContainer.addEventListener("scroll",this._boundScrollHandler,{passive:!0})}},{key:"_cleanupSeparatorScrollHandler",value:function(){this._boundScrollHandler&&this._optionsListContainer&&this._optionsListContainer.removeEventListener("scroll",this._boundScrollHandler)}},{key:"_handleSeparatorScroll",value:function(){if(this.pinSelectedItems&&this._separator&&this._optionsListContainer&&this._separatorContainer){var e=this._optionsListContainer.getBoundingClientRect(),t=this._separatorContainer.getBoundingClientRect().top-e.top,i=this._separatorScrollZone;if(t<=i&&t>=0){var o=1-t/i,r=this._separatorMinHeight+o*(this._separatorMaxHeight-this._separatorMinHeight);this._separator.setHeight(Math.round(r),!1)}else if(t>i){(this._separator.height||this._separatorMinHeight)!==this._separatorMinHeight&&this._separator.setHeight(this._separatorMinHeight,!1)}}}},{key:"_handleSeparatorClick",value:function(){this._optionsListContainer&&this._optionsListContainer.scrollTo({top:0,behavior:"smooth"})}},{key:"_applyFilterToOptions",value:function(e){if(!this.filterQuery)return e;var t=this.filterQuery.toLowerCase(),i=this.config,o=i.idField,r=i.primaryField,a=i.secondaryField,l=i.badgeField,s=i.custom,d=[];return o.filterable&&d.push((e=>e.idField)),r.filterable&&d.push((e=>e.primaryField)),a.filterable&&d.push((e=>e.secondaryField)),l.filterable&&d.push((e=>e.badgeField)),s&&Object.entries(s).forEach((e=>{var t=(0,n.A)(e,2),i=t[0];t[1].filterable&&d.push((e=>{var t=e[i];return"string"==typeof t?t:null==t?void 0:t.toString()}))})),e.filter((e=>d.some((i=>{var o=i(e);return"string"==typeof o&&o.toLowerCase().includes(t)}))))}},{key:"_sortOptions",value:function(e,t){var i=(arguments.length>2&&void 0!==arguments[2]?arguments[2]:k)===k?1:-1;return(0,r.A)(e).sort(((e,o)=>t(e,o)*i))}},{key:"_handleSearchChange",value:function(e){this.filterQuery=e.detail.value}},{key:"_handleSortButtonClick",value:function(e){var t;e.stopPropagation();var i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("knx-sort-menu");i&&i.openMenu(e.currentTarget)}},{key:"_handleSortChanged",value:function(e){this.sortCriterion=e.detail.criterion,this.sortDirection=e.detail.direction,(0,x.r)(this,"sort-changed",{criterion:this.sortCriterion,direction:this.sortDirection})}},{key:"_handlePinButtonClick",value:function(e){e.stopPropagation(),this.pinSelectedItems=!this.pinSelectedItems}},{key:"_handleClearFiltersButtonClick",value:function(e){e.stopPropagation(),e.preventDefault(),this._setSelectedOptions([])}},{key:"_setSelectedOptions",value:function(e){this.selectedOptions=e,(0,x.r)(this,"selection-changed",{value:this.selectedOptions})}},{key:"_getSortIcon",value:function(){return this.sortDirection===k?"M3 11H15V13H3M3 18V16H21V18M3 6H9V8H3Z":"M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"}},{key:"_hasFilterableOrSortableFields",value:function(){if(!this.config)return!1;var e=Object.values(this.config).filter((e=>e&&"object"==typeof e&&"filterable"in e)),t=this.config.custom?Object.values(this.config.custom):[];return[].concat((0,r.A)(e),(0,r.A)(t)).some((e=>e.filterable||e.sortable))}},{key:"_hasFilterableFields",value:function(){if(!this.config)return!1;var e=Object.values(this.config).filter((e=>e&&"object"==typeof e&&"filterable"in e)),t=this.config.custom?Object.values(this.config.custom):[];return[].concat((0,r.A)(e),(0,r.A)(t)).some((e=>e.filterable))}},{key:"_hasSortableFields",value:function(){if(!this.config)return!1;var e=Object.values(this.config).filter((e=>e&&"object"==typeof e&&"sortable"in e)),t=this.config.custom?Object.values(this.config.custom):[];return[].concat((0,r.A)(e),(0,r.A)(t)).some((e=>e.sortable))}},{key:"_expandedChanged",value:function(e){this.expanded=e.detail.expanded,(0,x.r)(this,"expanded-changed",{expanded:this.expanded})}},{key:"_handleOptionItemClick",value:function(e){var t=e.currentTarget.getAttribute("data-value");t&&this._toggleOption(t)}},{key:"_toggleOption",value:function(e){var t,i,o,n,a;null!==(t=null===(i=this.selectedOptions)||void 0===i?void 0:i.includes(e))&&void 0!==t&&t?this._setSelectedOptions(null!==(o=null===(n=this.selectedOptions)||void 0===n?void 0:n.filter((t=>t!==e)))&&void 0!==o?o:[]):this._setSelectedOptions([].concat((0,r.A)(null!==(a=this.selectedOptions)&&void 0!==a?a:[]),[e]));requestAnimationFrame((()=>{this._handleSeparatorScroll()}))}},{key:"_renderFilterControl",value:function(){var e;return(0,p.qy)(Z||(Z=ne`
      <div class="filter-toolbar">
        <div class="search">
          ${0}
        </div>
        ${0}
      </div>
    `),this._hasFilterableFields()?(0,p.qy)(q||(q=ne`
                <search-input-outlined
                  .hass=${0}
                  .filter=${0}
                  @value-changed=${0}
                ></search-input-outlined>
              `),this.hass,this.filterQuery,this._handleSearchChange):p.s6,this._hasSortableFields()?(0,p.qy)(j||(j=ne`
              <div class="buttons">
                <ha-icon-button
                  class="sort-button"
                  .path=${0}
                  title=${0}
                  @click=${0}
                ></ha-icon-button>

                <knx-sort-menu
                  .knx=${0}
                  .sortCriterion=${0}
                  .sortDirection=${0}
                  .isMobileDevice=${0}
                  @sort-changed=${0}
                >
                  <div slot="title">${0}</div>

                  <!-- Toolbar with additional controls like pin button -->
                  <div slot="toolbar">
                    <!-- Pin Button for keeping selected items at top -->
                    <ha-icon-button-toggle
                      .path=${0}
                      .selected=${0}
                      @click=${0}
                      title=${0}
                    >
                    </ha-icon-button-toggle>
                  </div>

                  <!-- Sort menu items generated from all sortable fields -->
                  ${0}
                </knx-sort-menu>
              </div>
            `),this._getSortIcon(),this.sortDirection===k?this.knx.localize("knx_list_filter_sort_ascending_tooltip"):this.knx.localize("knx_list_filter_sort_descending_tooltip"),this._handleSortButtonClick,this.knx,this.sortCriterion,this.sortDirection,this.isMobileDevice,this._handleSortChanged,this.knx.localize("knx_list_filter_sort_by"),"M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z",this.pinSelectedItems,this._handlePinButtonClick,this.knx.localize("knx_list_filter_selected_items_on_top"),[].concat((0,r.A)(Object.entries(this.config||{}).filter((e=>"custom"!==(0,n.A)(e,1)[0])).map((e=>{var t=(0,n.A)(e,2);return{key:t[0],config:t[1]}}))),(0,r.A)(Object.entries((null===(e=this.config)||void 0===e?void 0:e.custom)||{}).map((e=>{var t=(0,n.A)(e,2);return{key:t[0],config:t[1]}})))).filter((e=>e.config.sortable)).map((e=>{var t,i,o,r=e.key,n=e.config;return(0,p.qy)(N||(N=ne`
                        <knx-sort-menu-item
                          criterion=${0}
                          display-name=${0}
                          default-direction=${0}
                          ascending-text=${0}
                          descending-text=${0}
                          .disabled=${0}
                        ></knx-sort-menu-item>
                      `),r,(0,m.J)(n.fieldName),null!==(t=n.sortDefaultDirection)&&void 0!==t?t:"asc",null!==(i=n.sortAscendingText)&&void 0!==i?i:this.knx.localize("knx_list_filter_sort_ascending"),null!==(o=n.sortDescendingText)&&void 0!==o?o:this.knx.localize("knx_list_filter_sort_descending"),n.sortDisabled||!1)}))):p.s6)}},{key:"_renderOptionsList",value:function(){return(0,p.qy)(P||(P=ne`
      ${0}
    `),(0,v.a)([this.filterQuery,this.sortDirection,this.sortCriterion,this.data,this.selectedOptions,this.expanded,this.config,this.pinSelectedItems],(()=>this.pinSelectedItems?this._renderPinnedOptionsList():this._renderRegularOptionsList())))}},{key:"_renderPinnedOptionsList",value:function(){var e,t=this.knx.localize("knx_list_filter_no_results"),i=this._computeFilterSortedOptionsWithSeparator(),o=i.selected,r=i.unselected;return 0===o.length&&0===r.length?(0,p.qy)(R||(R=ne`<div class="empty-message" role="alert">${0}</div>`),t):(0,p.qy)(B||(B=ne`
      <div class="options-list" tabindex="0">
        <!-- Render selected items first -->
        ${0}

        <!-- Render separator between selected and unselected items -->
        ${0}

        <!-- Render unselected items -->
        ${0}
      </div>
    `),o.length>0?(0,p.qy)(U||(U=ne`
              ${0}
            `),(0,_.u)(o,(e=>e.idField),(e=>this._renderOptionItem(e)))):p.s6,o.length>0&&r.length>0?(0,p.qy)(W||(W=ne`
              <div class="separator-container">
                <knx-separator
                  .height=${0}
                  .maxHeight=${0}
                  .minHeight=${0}
                  .animationDuration=${0}
                  customClass="list-separator"
                >
                  <div class="separator-content" @click=${0}>
                    <ha-svg-icon .path=${0}></ha-svg-icon>
                    <span class="separator-text">
                      ${0}
                    </span>
                  </div>
                </knx-separator>
              </div>
            `),(null===(e=this._separator)||void 0===e?void 0:e.height)||this._separatorMinHeight,this._separatorMaxHeight,this._separatorMinHeight,this._separatorAnimationDuration,this._handleSeparatorClick,"M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z",this.knx.localize("knx_list_filter_scroll_to_selection")):p.s6,r.length>0?(0,p.qy)(K||(K=ne`
              ${0}
            `),(0,_.u)(r,(e=>e.idField),(e=>this._renderOptionItem(e)))):p.s6)}},{key:"_renderRegularOptionsList",value:function(){var e=this.knx.localize("knx_list_filter_no_results"),t=this._computeFilterSortedOptions();return 0===t.length?(0,p.qy)(G||(G=ne`<div class="empty-message" role="alert">${0}</div>`),e):(0,p.qy)(Q||(Q=ne`
      <div class="options-list" tabindex="0">
        ${0}
      </div>
    `),(0,_.u)(t,(e=>e.idField),(e=>this._renderOptionItem(e))))}},{key:"_renderOptionItem",value:function(e){var t={"option-item":!0,selected:e.selected};return(0,p.qy)(Y||(Y=ne`
      <div
        class=${0}
        role="option"
        aria-selected=${0}
        @click=${0}
        data-value=${0}
      >
        <div class="option-content">
          <div class="option-primary">
            <span class="option-label" title=${0}>${0}</span>
            ${0}
          </div>

          ${0}
        </div>

        <ha-checkbox
          .checked=${0}
          .value=${0}
          tabindex="-1"
          pointer-events="none"
        ></ha-checkbox>
      </div>
    `),(0,f.H)(t),e.selected,this._handleOptionItemClick,e.idField,e.primaryField,e.primaryField,e.badgeField?(0,p.qy)(J||(J=ne`<span class="option-badge">${0}</span>`),e.badgeField):p.s6,e.secondaryField?(0,p.qy)(X||(X=ne`
                <div class="option-secondary" title=${0}>
                  ${0}
                </div>
              `),e.secondaryField,e.secondaryField):p.s6,e.selected,e.idField)}},{key:"render",value:function(){var e,t,i=null!==(e=null===(t=this.selectedOptions)||void 0===t?void 0:t.length)&&void 0!==e?e:0,o=this.filterTitle||this.knx.localize("knx_list_filter_title"),r=this.knx.localize("knx_list_filter_clear");return(0,p.qy)(ee||(ee=ne`
      <flex-content-expansion-panel
        leftChevron
        .expanded=${0}
        @expanded-changed=${0}
      >
        <!-- Header with title and clear selection control -->
        <div slot="header" class="header">
          <span class="title">
            ${0}
            ${0}
          </span>
          <div class="controls">
            ${0}
          </div>
        </div>

        <!-- Render filter content only when panel is expanded and visible -->
        ${0}
      </flex-content-expansion-panel>
    `),this.expanded,this._expandedChanged,o,i?(0,p.qy)(te||(te=ne`<div class="badge">${0}</div>`),i):p.s6,i?(0,p.qy)(ie||(ie=ne`
                  <ha-icon-button
                    .path=${0}
                    @click=${0}
                    .title=${0}
                  ></ha-icon-button>
                `),"M21 8H3V6H21V8M13.81 16H10V18H13.09C13.21 17.28 13.46 16.61 13.81 16M18 11H6V13H18V11M21.12 15.46L19 17.59L16.88 15.46L15.47 16.88L17.59 19L15.47 21.12L16.88 22.54L19 20.41L21.12 22.54L22.54 21.12L20.41 19L22.54 16.88L21.12 15.46Z",this._handleClearFiltersButtonClick,r):p.s6,this.expanded?(0,p.qy)(oe||(oe=ne`
              <div class="filter-content">
                ${0}
              </div>

              <!-- Filter options list - moved outside filter-content for proper sticky behavior -->
              <div class="options-list-wrapper ha-scrollbar">${0}</div>
            `),this._hasFilterableOrSortableFields()?this._renderFilterControl():p.s6,this._renderOptionsList()):p.s6)}}],[{key:"styles",get:function(){return[y.dp,(0,p.AH)(re||(re=ne`
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
      `))]}}])}(p.WF);(0,h.__decorate)([(0,g.MZ)({attribute:!1,hasChanged:()=>!1})],ae.prototype,"hass",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:!1})],ae.prototype,"knx",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:!1})],ae.prototype,"data",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:!1})],ae.prototype,"selectedOptions",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:!1})],ae.prototype,"config",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],ae.prototype,"expanded",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean})],ae.prototype,"narrow",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean,attribute:"pin-selected-items"})],ae.prototype,"pinSelectedItems",void 0),(0,h.__decorate)([(0,g.MZ)({type:String,attribute:"filter-title"})],ae.prototype,"filterTitle",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:"filter-query"})],ae.prototype,"filterQuery",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:"sort-criterion"})],ae.prototype,"sortCriterion",void 0),(0,h.__decorate)([(0,g.MZ)({attribute:"sort-direction"})],ae.prototype,"sortDirection",void 0),(0,h.__decorate)([(0,g.MZ)({type:Boolean,attribute:"is-mobile-device"})],ae.prototype,"isMobileDevice",void 0),(0,h.__decorate)([(0,g.P)("knx-separator")],ae.prototype,"_separator",void 0),(0,h.__decorate)([(0,g.P)(".options-list-wrapper")],ae.prototype,"_optionsListContainer",void 0),(0,h.__decorate)([(0,g.P)(".separator-container")],ae.prototype,"_separatorContainer",void 0),ae=(0,h.__decorate)([(0,g.EM)("knx-list-filter")],ae)},31820:function(e,t,i){var o,r,n=i(44734),a=i(56038),l=i(69683),s=i(6454),d=(i(28706),i(62826)),c=i(96196),u=i(77845),h=e=>e,p=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(o))).showBorder=!1,e}return(0,s.A)(t,e),(0,a.A)(t,[{key:"render",value:function(){return(0,c.qy)(o||(o=h`
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
    `))}}],[{key:"styles",get:function(){return[(0,c.AH)(r||(r=h`
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
      `))]}}])}(c.WF);(0,d.__decorate)([(0,u.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],p.prototype,"showBorder",void 0),p=(0,d.__decorate)([(0,u.EM)("knx-dialog-header")],p)},10338:function(e,t,i){i.d(t,{K:function(){return w}});var o=i(94741),r=i(61397),n=i(50264),a=i(31432),l=i(78261),s=i(44734),d=i(56038),c=(i(16280),i(28706),i(2008),i(48980),i(74423),i(23792),i(62062),i(26910),i(18111),i(81148),i(22489),i(7588),i(61701),i(33110),i(5506),i(26099),i(27495),i(38781),i(5746),i(23500),i(62953),i(48408),i(14603),i(47566),i(98721),i(5871)),u=i(76679),h=i(22786),p=i(65294),g=(i(50113),i(44114),i(54554),i(20116),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),function(){return(0,d.A)((function e(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:2e3;(0,s.A)(this,e),this._maxSize=t,this._buffer=[]}),[{key:"add",value:function(e){var t=Array.isArray(e)?e:[e];if(0===this._buffer.length){var i;(i=this._buffer).push.apply(i,(0,o.A)(t)),t.length>1&&this._buffer.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0))}else{var r,n,a=this._buffer[this._buffer.length-1].timestampIso,l=t.every((e=>e.timestampIso>=a)),s=t.length<=1||t.every(((e,i)=>0===i||t[i-1].timestampIso<=e.timestampIso));if(l&&s)(r=this._buffer).push.apply(r,(0,o.A)(t));else(n=this._buffer).push.apply(n,(0,o.A)(t)),this._buffer.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0))}if(this._buffer.length>this._maxSize){var d=this._buffer.length-this._maxSize;return this._buffer.splice(0,d)}return[]}},{key:"merge",value:function(e){var t=new Set(this._buffer.map((e=>e.id))),i=e.filter((e=>!t.has(e.id)));return i.sort(((e,t)=>e.timestampIso<t.timestampIso?-1:e.timestampIso>t.timestampIso?1:0)),{added:i,removed:this.add(i)}}},{key:"setMaxSize",value:function(e){if(this._maxSize=e,this._buffer.length>e){var t=this._buffer.length-e;return this._buffer.splice(0,t)}return[]}},{key:"maxSize",get:function(){return this._maxSize}},{key:"length",get:function(){return this._buffer.length}},{key:"snapshot",get:function(){return(0,o.A)(this._buffer)}},{key:"clear",value:function(){var e=(0,o.A)(this._buffer);return this._buffer.length=0,e}},{key:"isEmpty",get:function(){return 0===this._buffer.length}},{key:"at",value:function(e){return this._buffer[e]}},{key:"findIndexById",value:function(e){return this._buffer.findIndex((t=>t.id===e))}},{key:"getById",value:function(e){return this._buffer.find((t=>t.id===e))}}])}()),f=i(78577),v=new f.Q("connection_service"),m=function(){return(0,d.A)((function e(){(0,s.A)(this,e),this._connectionError=null,this._onTelegram=null,this._onConnectionChange=null}),[{key:"connectionError",get:function(){return this._connectionError}},{key:"isConnected",get:function(){return!!this._subscribed}},{key:"onTelegram",value:function(e){this._onTelegram=e}},{key:"onConnectionChange",value:function(e){this._onConnectionChange=e}},{key:"subscribe",value:(t=(0,n.A)((0,r.A)().m((function e(t){var i;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(!this._subscribed){e.n=1;break}return v.warn("Already subscribed to telegrams"),e.a(2);case 1:return e.p=1,e.n=2,(0,p.EE)(t,(e=>{this._onTelegram&&this._onTelegram(e)}));case 2:this._subscribed=e.v,this._connectionError=null,this._notifyConnectionChange(!0),v.debug("Successfully subscribed to telegrams"),e.n=4;break;case 3:throw e.p=3,i=e.v,v.error("Failed to subscribe to telegrams",i),this._connectionError=i instanceof Error?i.message:String(i),this._notifyConnectionChange(!1,this._connectionError),i;case 4:return e.a(2)}}),e,this,[[1,3]])}))),function(e){return t.apply(this,arguments)})},{key:"unsubscribe",value:function(){this._subscribed&&(this._subscribed(),this._subscribed=void 0,this._notifyConnectionChange(!1),v.debug("Unsubscribed from telegrams"))}},{key:"reconnect",value:(e=(0,n.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return this._connectionError=null,this._notifyConnectionChange(!1),e.n=1,this.subscribe(t);case 1:return e.a(2)}}),e,this)}))),function(t){return e.apply(this,arguments)})},{key:"clearError",value:function(){this._connectionError=null,this._notifyConnectionChange(this.isConnected)}},{key:"disconnect",value:function(){this.unsubscribe(),this._onTelegram=null,this._onConnectionChange=null}},{key:"_notifyConnectionChange",value:function(e,t){this._onConnectionChange&&this._onConnectionChange(e,t)}}]);var e,t}(),_=i(93777),b=i(25474),y=(0,d.A)((function e(t){(0,s.A)(this,e),this.offset=null,this.id=(0,_.Y)(`${t.timestamp}_${t.source}_${t.destination}`),this.timestampIso=t.timestamp,this.timestamp=new Date(t.timestamp),this.sourceAddress=t.source,this.sourceText=t.source_name,this.sourceName=`${t.source}: ${t.source_name}`,this.destinationAddress=t.destination,this.destinationText=t.destination_name,this.destinationName=`${t.destination}: ${t.destination_name}`,this.type=t.telegramtype,this.direction=t.direction,this.payload=b.e4.payload(t),this.dpt=b.e4.dptNameNumber(t),this.unit=t.unit,this.value=b.e4.valueWithUnit(t)||this.payload||("GroupValueRead"===t.telegramtype?"GroupRead":"")})),x=new f.Q("group_monitor_controller"),k=["source","destination","direction","telegramtype"],w=function(){function e(t){(0,s.A)(this,e),this._connectionService=new m,this._telegramBuffer=new g(2e3),this._selectedTelegramId=null,this._filters={},this._sortColumn="timestampIso",this._sortDirection="desc",this._expandedFilter="source",this._isReloadEnabled=!1,this._isPaused=!1,this._isProjectLoaded=void 0,this._connectionError=null,this._distinctValues={source:{},destination:{},direction:{},telegramtype:{}},this._bufferVersion=0,this._getFilteredTelegramsAndDistinctValues=(0,h.A)(((e,t,i,o,r,n)=>{var s=i.filter((e=>this.matchesActiveFilters(e)));r&&n&&s.sort(((e,t)=>{var i,o,a;switch(r){case"timestampIso":i=e.timestampIso,o=t.timestampIso;break;case"sourceAddress":i=e.sourceAddress,o=t.sourceAddress;break;case"destinationAddress":i=e.destinationAddress,o=t.destinationAddress;break;case"sourceText":i=e.sourceText||"",o=t.sourceText||"";break;case"destinationText":i=e.destinationText||"",o=t.destinationText||"";break;default:i=e[r]||"",o=t[r]||""}return a="string"==typeof i&&"string"==typeof o?i.localeCompare(o):i<o?-1:i>o?1:0,"asc"===n?a:-a}));for(var d={source:{},destination:{},direction:{},telegramtype:{}},c=Object.keys(o),u=0,h=c;u<h.length;u++)for(var p=h[u],g=0,f=Object.entries(o[p]);g<f.length;g++){var v=(0,l.A)(f[g],2),m=v[0],_=v[1];d[p][m]={id:_.id,name:_.name,totalCount:_.totalCount,filteredCount:0}}for(var b=0;b<s.length;b++){var y=s[b];if("timestampIso"===r&&n||!r){var x=null;x="desc"===n&&r?b<s.length-1?s[b+1]:null:b>0?s[b-1]:null,y.offset=this._calculateTelegramOffset(y,x)}else y.offset=null;var k,w=(0,a.A)(c);try{for(w.s();!(k=w.n()).done;){var $=k.value,A=this._extractTelegramField(y,$);if(A){var C=A.id,F=d[$][C];F&&(F.filteredCount=(F.filteredCount||0)+1)}}}catch(T){w.e(T)}finally{w.f()}}return{filteredTelegrams:s,distinctValues:d}})),this.host=t,t.addController(this),this._connectionService.onTelegram((e=>this._handleIncomingTelegram(e))),this._connectionService.onConnectionChange(((e,t)=>{this._connectionError=t||null,this.host.requestUpdate()}))}return(0,d.A)(e,[{key:"hostConnected",value:function(){this._setFiltersFromUrl()}},{key:"hostDisconnected",value:function(){this._connectionService.disconnect()}},{key:"setup",value:(_=(0,n.A)((0,r.A)().m((function e(t){var i;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(!this._connectionService.isConnected){e.n=1;break}return e.a(2);case 1:return e.n=2,this._loadRecentTelegrams(t);case 2:if(e.v){e.n=3;break}return e.a(2);case 3:return e.p=3,e.n=4,this._connectionService.subscribe(t);case 4:e.n=6;break;case 5:e.p=5,i=e.v,x.error("Failed to setup connection",i),this._connectionError=i instanceof Error?i.message:String(i),this.host.requestUpdate();case 6:return e.a(2)}}),e,this,[[3,5]])}))),function(e){return _.apply(this,arguments)})},{key:"telegrams",get:function(){return this._telegramBuffer.snapshot}},{key:"selectedTelegramId",get:function(){return this._selectedTelegramId},set:function(e){this._selectedTelegramId=e,this.host.requestUpdate()}},{key:"filters",get:function(){return this._filters}},{key:"sortColumn",get:function(){return this._sortColumn},set:function(e){this._sortColumn=e,this.host.requestUpdate()}},{key:"sortDirection",get:function(){return this._sortDirection},set:function(e){this._sortDirection=e||"desc",this.host.requestUpdate()}},{key:"expandedFilter",get:function(){return this._expandedFilter}},{key:"isReloadEnabled",get:function(){return this._isReloadEnabled}},{key:"isPaused",get:function(){return this._isPaused}},{key:"isProjectLoaded",get:function(){return this._isProjectLoaded}},{key:"connectionError",get:function(){return this._connectionError}},{key:"getFilteredTelegramsAndDistinctValues",value:function(){return this._getFilteredTelegramsAndDistinctValues(this._bufferVersion,JSON.stringify(this._filters),this._telegramBuffer.snapshot,this._distinctValues,this._sortColumn,this._sortDirection)}},{key:"matchesActiveFilters",value:function(e){return Object.entries(this._filters).every((t=>{var i=(0,l.A)(t,2),o=i[0],r=i[1];if(null==r||!r.length)return!0;var n={source:e.sourceAddress,destination:e.destinationAddress,direction:e.direction,telegramtype:e.type};return r.includes(n[o]||"")}))}},{key:"toggleFilterValue",value:function(e,t,i){var r,n=null!==(r=this._filters[e])&&void 0!==r?r:[];n.includes(t)?this._filters=Object.assign(Object.assign({},this._filters),{},{[e]:n.filter((e=>e!==t))}):this._filters=Object.assign(Object.assign({},this._filters),{},{[e]:[].concat((0,o.A)(n),[t])}),this._updateUrlFromFilters(i),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}},{key:"setFilterFieldValue",value:function(e,t,i){this._filters=Object.assign(Object.assign({},this._filters),{},{[e]:t}),this._updateUrlFromFilters(i),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}},{key:"clearFilters",value:function(e){this._filters={},this._updateUrlFromFilters(e),this._cleanupUnusedFilterValues(),this.host.requestUpdate()}},{key:"updateExpandedFilter",value:function(e,t){this._expandedFilter=t?e:this._expandedFilter===e?null:this._expandedFilter,this.host.requestUpdate()}},{key:"togglePause",value:(v=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:this._isPaused=!this._isPaused,this.host.requestUpdate();case 1:return e.a(2)}}),e,this)}))),function(){return v.apply(this,arguments)})},{key:"reload",value:(f=(0,n.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this._loadRecentTelegrams(t);case 1:return e.a(2)}}),e,this)}))),function(e){return f.apply(this,arguments)})},{key:"retryConnection",value:(i=(0,n.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this._connectionService.reconnect(t);case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"clearTelegrams",value:function(){var e=this._createFilteredDistinctValues();this._telegramBuffer.clear(),this._resetDistinctValues(e),this._isReloadEnabled=!0,this.host.requestUpdate()}},{key:"navigateTelegram",value:function(e,t){if(this._selectedTelegramId){var i=t.findIndex((e=>e.id===this._selectedTelegramId))+e;i>=0&&i<t.length&&(this._selectedTelegramId=t[i].id,this.host.requestUpdate())}}},{key:"_calculateTelegramOffset",value:function(e,t){return t?(0,b.u_)(e.timestampIso)-(0,b.u_)(t.timestampIso):null}},{key:"_extractTelegramField",value:function(e,t){switch(t){case"source":return{id:e.sourceAddress,name:e.sourceText||""};case"destination":return{id:e.destinationAddress,name:e.destinationText||""};case"direction":return{id:e.direction,name:""};case"telegramtype":return{id:e.type,name:""};default:return null}}},{key:"_addToDistinctValues",value:function(e){for(var t=0,i=k;t<i.length;t++){var o=i[t],r=this._extractTelegramField(e,o);if(r){var n=r.id,a=r.name;this._distinctValues[o][n]||(this._distinctValues[o][n]={id:n,name:a,totalCount:0}),this._distinctValues[o][n].totalCount++,""===this._distinctValues[o][n].name&&a&&(this._distinctValues[o][n].name=a)}else x.warn(`Unknown field for distinct values: ${o}`)}this._bufferVersion++}},{key:"_removeFromDistinctValues",value:function(e){if(0!==e.length){var t,i=(0,a.A)(e);try{for(i.s();!(t=i.n()).done;)for(var o=t.value,r=0,n=k;r<n.length;r++){var l=n[r],s=this._extractTelegramField(o,l);if(s){var d=s.id,c=this._distinctValues[l][d];c&&(c.totalCount--,c.totalCount<=0&&delete this._distinctValues[l][d])}}}catch(u){i.e(u)}finally{i.f()}this._bufferVersion++}}},{key:"_createFilteredDistinctValues",value:function(){for(var e={source:{},destination:{},direction:{},telegramtype:{}},t=0,i=k;t<i.length;t++){var o=i[t],r=this._filters[o];if(null!=r&&r.length){var n,l=(0,a.A)(r);try{for(l.s();!(n=l.n()).done;){var s=n.value,d=this._distinctValues[o][s];e[o][s]={id:s,name:(null==d?void 0:d.name)||"",totalCount:0}}}catch(c){l.e(c)}finally{l.f()}}}return e}},{key:"_cleanupUnusedFilterValues",value:function(){for(var e=!1,t=0,i=k;t<i.length;t++)for(var o=i[t],r=this._filters[o]||[],n=this._distinctValues[o],a=0,s=Object.entries(n);a<s.length;a++){var d=(0,l.A)(s[a],2),c=d[0];0!==d[1].totalCount||r.includes(c)||(delete this._distinctValues[o][c],e=!0)}e&&this._bufferVersion++}},{key:"_resetDistinctValues",value:function(e){this._distinctValues=e?{source:Object.assign({},e.source),destination:Object.assign({},e.destination),direction:Object.assign({},e.direction),telegramtype:Object.assign({},e.telegramtype)}:{source:{},destination:{},direction:{},telegramtype:{}},this._bufferVersion++}},{key:"_calculateTelegramStorageBuffer",value:function(t){var i=Math.ceil(.1*t),o=100*Math.ceil(i/100);return Math.max(o,e.MIN_TELEGRAM_STORAGE_BUFFER)}},{key:"_loadRecentTelegrams",value:(t=(0,n.A)((0,r.A)().m((function e(t){var i,o,n,l,s,d,c,u,h,g,f,v,m;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.p=0,e.n=1,(0,p.eq)(t);case 1:if(i=e.v,this._isProjectLoaded=i.project_loaded,o=i.recent_telegrams.length,n=this._calculateTelegramStorageBuffer(o),l=o+n,this._telegramBuffer.maxSize!==l&&(s=this._telegramBuffer.setMaxSize(l)).length>0&&this._removeFromDistinctValues(s),d=i.recent_telegrams.map((e=>new y(e))),c=this._telegramBuffer.merge(d),u=c.added,(h=c.removed).length>0&&this._removeFromDistinctValues(h),u.length>0){g=(0,a.A)(u);try{for(g.s();!(f=g.n()).done;)v=f.value,this._addToDistinctValues(v)}catch(r){g.e(r)}finally{g.f()}}return null!==this._connectionError&&(this._connectionError=null),this._isReloadEnabled=!1,(u.length>0||null===this._connectionError)&&this.host.requestUpdate(),e.a(2,!0);case 2:return e.p=2,m=e.v,x.error("getGroupMonitorInfo failed",m),this._connectionError=m instanceof Error?m.message:String(m),this.host.requestUpdate(),e.a(2,!1)}}),e,this,[[0,2]])}))),function(e){return t.apply(this,arguments)})},{key:"_handleIncomingTelegram",value:function(e){var t=new y(e);if(this._isPaused)this._isReloadEnabled||(this._isReloadEnabled=!0,this.host.requestUpdate());else{var i=this._telegramBuffer.add(t);i.length>0&&this._removeFromDistinctValues(i),this._addToDistinctValues(t),this.host.requestUpdate()}}},{key:"_updateUrlFromFilters",value:function(e){if(e){var t=new URLSearchParams;Object.entries(this._filters).forEach((e=>{var i=(0,l.A)(e,2),o=i[0],r=i[1];Array.isArray(r)&&r.length>0&&t.set(o,r.join(","))}));var i=t.toString()?`${e.prefix}${e.path}?${t.toString()}`:`${e.prefix}${e.path}`;(0,c.o)(decodeURIComponent(i),{replace:!0})}else x.warn("Route not available, cannot update URL")}},{key:"_setFiltersFromUrl",value:function(){var e=new URLSearchParams(u.G.location.search),t=e.get("source"),i=e.get("destination"),o=e.get("direction"),r=e.get("telegramtype");if(t||i||o||r){this._filters={source:t?t.split(","):[],destination:i?i.split(","):[],direction:o?o.split(","):[],telegramtype:r?r.split(","):[]};var n=this._createFilteredDistinctValues();this._resetDistinctValues(n),this.host.requestUpdate()}}}]);var t,i,f,v,_}();w.MIN_TELEGRAM_STORAGE_BUFFER=1e3},4597:function(e,t,i){i.a(e,(async function(e,t){try{var o=i(44734),r=i(56038),n=i(69683),a=i(6454),l=i(25460),s=(i(28706),i(62826)),d=i(96196),c=i(77845),u=i(92542),h=i(39396),p=(i(60961),i(89473)),g=(i(31820),i(25474)),f=i(18043),v=(i(60733),i(95637),e([p,f]));[p,f]=v.then?(await v)():v;var m,_,b,y,x,k,w,$=e=>e,A=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,r=new Array(i),a=0;a<i;a++)r[a]=arguments[a];return(e=(0,n.A)(this,t,[].concat(r))).narrow=!1,e.disableNext=!1,e.disablePrevious=!1,e}return(0,a.A)(t,e),(0,r.A)(t,[{key:"connectedCallback",value:function(){(0,l.A)(t,"connectedCallback",this,3)([]),this._handleKeyDown=this._handleKeyDown.bind(this),document.addEventListener("keydown",this._handleKeyDown)}},{key:"disconnectedCallback",value:function(){document.removeEventListener("keydown",this._handleKeyDown),(0,l.A)(t,"disconnectedCallback",this,3)([])}},{key:"closeDialog",value:function(){this.telegram=void 0,(0,u.r)(this,"dialog-closed",{dialog:this.localName},{bubbles:!1})}},{key:"_checkScrolled",value:function(e){var t,i=e.target,o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("knx-dialog-header");o&&i.scrollTop>0?o.showBorder=!0:o&&(o.showBorder=!1)}},{key:"render",value:function(){if(!this.telegram)return this.closeDialog(),d.s6;var e="Outgoing"===this.telegram.direction?"outgoing":"incoming";return(0,d.qy)(m||(m=$`
      <!-- 
        The .heading property is required for the header slot to be rendered,
        even though we override it with our custom knx-dialog-header component.
        The value is not displayed but must be truthy for the slot to work.
      -->
      <ha-dialog open @closed=${0} .heading=${0}>
        <knx-dialog-header slot="heading" .showBorder=${0}>
          <ha-icon-button
            slot="navigationIcon"
            .label=${0}
            .path=${0}
            dialogAction="close"
            class="close-button"
          ></ha-icon-button>
          <div slot="title" class="header-title">
            ${0}
          </div>
          <div slot="subtitle">
            <span title=${0}>
              ${0}
            </span>
            ${0}
          </div>
          <div slot="actionItems" class="direction-badge ${0}">
            ${0}
          </div>
        </knx-dialog-header>
        <div class="content" @scroll=${0}>
          <!-- Body: addresses + value + details -->
          <div class="telegram-body">
            <div class="addresses-row">
              <div class="address-item">
                <div class="item-label">
                  ${0}
                </div>
                <div class="address-chip">${0}</div>
                ${0}
              </div>
              <div class="address-item">
                <div class="item-label">
                  ${0}
                </div>
                <div class="address-chip">${0}</div>
                ${0}
              </div>
            </div>

            ${0}

            <div class="telegram-details">
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="detail-label">
                    ${0}
                  </div>
                  <div class="detail-value">${0}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-label">DPT</div>
                  <div class="detail-value">${0}</div>
                </div>
                ${0}
              </div>
            </div>
          </div>
        </div>

        <!-- Navigation buttons: previous / next -->
        <div slot="secondaryAction">
          <ha-button
            appearance="plain"
            @click=${0}
            .disabled=${0}
          >
            <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
            ${0}
          </ha-button>
        </div>
        <div slot="primaryAction" class="primaryAction">
          <ha-button appearance="plain" @click=${0} .disabled=${0}>
            ${0}
            <ha-svg-icon .path=${0} slot="end"></ha-svg-icon>
          </ha-button>
        </div>
      </ha-dialog>
    `),this.closeDialog," ",!0,this.knx.localize("ui.dialogs.generic.close"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",this.knx.localize("knx_telegram_info_dialog_telegram"),(0,g.CY)(this.telegram.timestampIso),(0,g.HF)(this.telegram.timestamp)+" ",this.narrow?d.s6:(0,d.qy)(_||(_=$`
                  (<ha-relative-time
                    .hass=${0}
                    .datetime=${0}
                    .capitalize=${0}
                  ></ha-relative-time
                  >)
                `),this.hass,this.telegram.timestamp,!1),e,this.knx.localize(this.telegram.direction),this._checkScrolled,this.knx.localize("knx_telegram_info_dialog_source"),this.telegram.sourceAddress,this.telegram.sourceText?(0,d.qy)(b||(b=$`<div class="item-name">${0}</div>`),this.telegram.sourceText):d.s6,this.knx.localize("knx_telegram_info_dialog_destination"),this.telegram.destinationAddress,this.telegram.destinationText?(0,d.qy)(y||(y=$`<div class="item-name">${0}</div>`),this.telegram.destinationText):d.s6,null!=this.telegram.value?(0,d.qy)(x||(x=$`
                  <div class="value-section">
                    <div class="value-label">
                      ${0}
                    </div>
                    <div class="value-content">${0}</div>
                  </div>
                `),this.knx.localize("knx_telegram_info_dialog_value"),this.telegram.value):d.s6,this.knx.localize("knx_telegram_info_dialog_type"),this.telegram.type,this.telegram.dpt||"",null!=this.telegram.payload?(0,d.qy)(k||(k=$`
                      <div class="detail-item payload">
                        <div class="detail-label">
                          ${0}
                        </div>
                        <code>${0}</code>
                      </div>
                    `),this.knx.localize("knx_telegram_info_dialog_payload"),this.telegram.payload):d.s6,this._previousTelegram,this.disablePrevious,"M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z",this.hass.localize("ui.common.previous"),this._nextTelegram,this.disableNext,this.hass.localize("ui.common.next"),"M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z")}},{key:"_nextTelegram",value:function(){(0,u.r)(this,"next-telegram",void 0,{bubbles:!0})}},{key:"_previousTelegram",value:function(){(0,u.r)(this,"previous-telegram",void 0,{bubbles:!0})}},{key:"_handleKeyDown",value:function(e){if(this.telegram)switch(e.key){case"ArrowLeft":case"ArrowDown":this.disablePrevious||(e.preventDefault(),this._previousTelegram());break;case"ArrowRight":case"ArrowUp":this.disableNext||(e.preventDefault(),this._nextTelegram())}}}],[{key:"styles",get:function(){return[h.nA,(0,d.AH)(w||(w=$`
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
      `))]}}])}(d.WF);(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"knx",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"narrow",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"telegram",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"disableNext",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"disablePrevious",void 0),A=(0,s.__decorate)([(0,c.EM)("knx-group-monitor-telegram-info-dialog")],A),t()}catch(C){t(C)}}))},84315:function(e,t,i){i.a(e,(async function(e,o){try{i.r(t),i.d(t,{KNXGroupMonitor:function(){return q}});var r=i(61397),n=i(50264),a=i(44734),l=i(56038),s=i(75864),d=i(69683),c=i(6454),u=(i(28706),i(2008),i(48980),i(74423),i(18111),i(22489),i(13579),i(26099),i(16034),i(38781),i(62826)),h=i(96196),p=i(22786),g=i(54393),f=i(91130),v=(i(17963),i(89473)),m=(i(60733),i(21912)),_=i(80111),b=(i(41508),i(7791),i(4597)),y=(i(1002),i(77845)),x=i(25474),k=i(10338),w=e([g,f,v,b]);[g,f,v,b]=w.then?(await w)():w;var $,A,C,F,T,S,D,M,z,L,H,I,O,E,V,Z=e=>e,q=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),r=0;r<i;r++)o[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(o))).controller=new k.K((0,s.A)(e)),e._sourceFilterConfig=(0,p.A)(((t,i,o,r)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{fieldName:e.knx.localize("telegram_filter_source_sort_by_primaryText"),filterable:!0,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.id},secondaryField:{fieldName:e.knx.localize("telegram_filter_source_sort_by_secondaryText"),filterable:!0,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.name},badgeField:{fieldName:e.knx.localize("telegram_filter_source_sort_by_badge"),filterable:!1,sortable:!1,mapper:e=>t?`${e.filteredCount}/${e.totalCount}`:`${e.totalCount}`},custom:{totalCount:{fieldName:e.knx.localize("telegram_filter_sort_by_total_count"),filterable:!1,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>e.totalCount.toString()},filteredCount:{fieldName:e.knx.localize("telegram_filter_sort_by_filtered_count"),filterable:!1,sortable:i>0||"filteredCount"===o,sortDisabled:0===i,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>(e.filteredCount||0).toString()}}}))),e._destinationFilterConfig=(0,p.A)(((t,i,o,r)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{fieldName:e.knx.localize("telegram_filter_destination_sort_by_primaryText"),filterable:!0,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.id},secondaryField:{fieldName:e.knx.localize("telegram_filter_destination_sort_by_secondaryText"),filterable:!0,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"asc",mapper:e=>e.name},badgeField:{fieldName:e.knx.localize("telegram_filter_destination_sort_by_badge"),filterable:!1,sortable:!1,mapper:e=>t?`${e.filteredCount}/${e.totalCount}`:`${e.totalCount}`},custom:{totalCount:{fieldName:e.knx.localize("telegram_filter_sort_by_total_count"),filterable:!1,sortable:!0,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>e.totalCount.toString()},filteredCount:{fieldName:e.knx.localize("telegram_filter_sort_by_filtered_count"),filterable:!1,sortable:i>0||"filteredCount"===o,sortDisabled:0===i,sortAscendingText:e.knx.localize("telegram_filter_sort_ascending"),sortDescendingText:e.knx.localize("telegram_filter_sort_descending"),sortDefaultDirection:"desc",mapper:e=>(e.filteredCount||0).toString()}}}))),e._directionFilterConfig=(0,p.A)(((e,t)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{filterable:!1,sortable:!1,mapper:e=>e.id},secondaryField:{filterable:!1,sortable:!1,mapper:e=>e.name},badgeField:{filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`}}))),e._telegramTypeFilterConfig=(0,p.A)(((e,t)=>({idField:{filterable:!1,sortable:!1,mapper:e=>e.id},primaryField:{filterable:!1,sortable:!1,mapper:e=>e.id},secondaryField:{filterable:!1,sortable:!1,mapper:e=>e.name},badgeField:{filterable:!1,sortable:!1,mapper:t=>e?`${t.filteredCount}/${t.totalCount}`:`${t.totalCount}`}}))),e._onFilterSelectionChange=(t,i)=>{e.controller.setFilterFieldValue(t,i,e.route)},e._onFilterExpansionChange=(t,i)=>{e.controller.updateExpandedFilter(t,i)},e._handleSourceFilterChange=t=>{e._onFilterSelectionChange("source",t.detail.value)},e._handleSourceFilterExpanded=t=>{e._onFilterExpansionChange("source",t.detail.expanded)},e._handleDestinationFilterChange=t=>{e._onFilterSelectionChange("destination",t.detail.value)},e._handleDestinationFilterExpanded=t=>{e._onFilterExpansionChange("destination",t.detail.expanded)},e._handleDirectionFilterChange=t=>{e._onFilterSelectionChange("direction",t.detail.value)},e._handleDirectionFilterExpanded=t=>{e._onFilterExpansionChange("direction",t.detail.expanded)},e._handleTelegramTypeFilterChange=t=>{e._onFilterSelectionChange("telegramtype",t.detail.value)},e._handleTelegramTypeFilterExpanded=t=>{e._onFilterExpansionChange("telegramtype",t.detail.expanded)},e._handleSourceFilterToggle=t=>{e.controller.toggleFilterValue("source",t.detail.value,e.route)},e._handleDestinationFilterToggle=t=>{e.controller.toggleFilterValue("destination",t.detail.value,e.route)},e._handleTelegramTypeFilterToggle=t=>{e.controller.toggleFilterValue("telegramtype",t.detail.value,e.route)},e._handleFilterSortChanged=t=>{e.requestUpdate()},e._columns=(0,p.A)(((t,i,o)=>({timestampIso:{showNarrow:!1,filterable:!0,sortable:!0,direction:"desc",title:e.knx.localize("group_monitor_time"),minWidth:"110px",maxWidth:"122px",template:t=>(0,h.qy)($||($=Z`
          <knx-table-cell>
            <div class="primary" slot="primary">${0}</div>
            ${0}
          </knx-table-cell>
        `),(0,x.Zc)(t.timestamp),null===t.offset||"timestampIso"!==e.controller.sortColumn&&void 0!==e.controller.sortColumn?h.s6:(0,h.qy)(A||(A=Z`
                  <div class="secondary" slot="secondary">
                    <span>+</span>
                    <span>${0}</span>
                  </div>
                `),e._formatOffsetWithPrecision(t.offset)))},sourceAddress:{showNarrow:!0,filterable:!0,sortable:!0,title:e.knx.localize("group_monitor_source"),flex:2,minWidth:"0",template:t=>(0,h.qy)(C||(C=Z`
          <knx-table-cell-filterable
            .knx=${0}
            .filterValue=${0}
            .filterDisplayText=${0}
            .filterActive=${0}
            .filterDisabled=${0}
            @toggle-filter=${0}
          >
            <div class="primary" slot="primary">${0}</div>
            ${0}
          </knx-table-cell-filterable>
        `),e.knx,t.sourceAddress,t.sourceAddress,(e.controller.filters.source||[]).includes(t.sourceAddress),e.isMobileTouchDevice,e._handleSourceFilterToggle,t.sourceAddress,t.sourceText?(0,h.qy)(F||(F=Z`
                  <div class="secondary" slot="secondary" title=${0}>
                    ${0}
                  </div>
                `),t.sourceText||"",t.sourceText):h.s6)},sourceText:{hidden:!0,filterable:!0,sortable:!0,title:e.knx.localize("group_monitor_source_name")},sourceName:{showNarrow:!0,hidden:!0,sortable:!1,groupable:!0,filterable:!1,title:e.knx.localize("group_monitor_source")},destinationAddress:{showNarrow:!0,sortable:!0,filterable:!0,title:e.knx.localize("group_monitor_destination"),flex:2,minWidth:"0",template:t=>(0,h.qy)(T||(T=Z`
          <knx-table-cell-filterable
            .knx=${0}
            .filterValue=${0}
            .filterDisplayText=${0}
            .filterActive=${0}
            .filterDisabled=${0}
            @toggle-filter=${0}
          >
            <div class="primary" slot="primary">${0}</div>
            ${0}
          </knx-table-cell-filterable>
        `),e.knx,t.destinationAddress,t.destinationAddress,(e.controller.filters.destination||[]).includes(t.destinationAddress),e.isMobileTouchDevice,e._handleDestinationFilterToggle,t.destinationAddress,t.destinationText?(0,h.qy)(S||(S=Z`
                  <div class="secondary" slot="secondary" title=${0}>
                    ${0}
                  </div>
                `),t.destinationText||"",t.destinationText):h.s6)},destinationText:{showNarrow:!0,hidden:!0,sortable:!0,filterable:!0,title:e.knx.localize("group_monitor_destination_name")},destinationName:{showNarrow:!0,hidden:!0,sortable:!1,groupable:!0,filterable:!1,title:e.knx.localize("group_monitor_destination")},type:{showNarrow:!1,title:e.knx.localize("group_monitor_type"),filterable:!0,sortable:!0,groupable:!0,minWidth:"155px",maxWidth:"155px",template:t=>(0,h.qy)(D||(D=Z`
          <knx-table-cell-filterable
            .knx=${0}
            .filterValue=${0}
            .filterDisplayText=${0}
            .filterActive=${0}
            .filterDisabled=${0}
            @toggle-filter=${0}
          >
            <div class="primary" slot="primary" title=${0}>${0}</div>
            <div
              class="secondary"
              slot="secondary"
              style="color: ${0}"
            >
              ${0}
            </div>
          </knx-table-cell-filterable>
        `),e.knx,t.type,t.type,(e.controller.filters.telegramtype||[]).includes(t.type),e.isMobileTouchDevice,e._handleTelegramTypeFilterToggle,t.type,t.type,"Outgoing"===t.direction?"var(--knx-blue)":"var(--knx-green)",t.direction)},direction:{hidden:!0,title:e.knx.localize("group_monitor_direction"),filterable:!0,groupable:!0},payload:{showNarrow:!1,hidden:t&&i,title:e.knx.localize("group_monitor_payload"),filterable:!0,sortable:!0,type:"numeric",minWidth:"105px",maxWidth:"105px",template:e=>e.payload?(0,h.qy)(M||(M=Z`
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
              title=${0}
            >
              ${0}
            </code>
          `),e.payload,e.payload):h.s6},value:{showNarrow:!0,hidden:!i,title:e.knx.localize("group_monitor_value"),filterable:!0,sortable:!0,flex:1,minWidth:"0",template:e=>{var t=e.value;return t?(0,h.qy)(z||(z=Z`
            <knx-table-cell>
              <span
                class="primary"
                slot="primary"
                style="font-weight: 500; color: var(--primary-color);"
                title=${0}
              >
                ${0}
              </span>
            </knx-table-cell>
          `),t,t):h.s6}}}))),e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"isMobileTouchDevice",get:function(){return m.M&&_.C}},{key:"_getFilteredData",value:function(){return this.controller.getFilteredTelegramsAndDistinctValues()}},{key:"firstUpdated",value:(g=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.controller.setup(this.hass);case 1:return e.a(2)}}),e,this)}))),function(){return g.apply(this,arguments)})},{key:"searchLabel",get:function(){if(this.narrow)return this.knx.localize("group_monitor_search_label_narrow");var e=this._getFilteredData().filteredTelegrams.length,t=1===e?"group_monitor_search_label_singular":"group_monitor_search_label";return this.knx.localize(t,{count:e})}},{key:"_hasActiveFilters",value:function(e){if(e){var t=this.controller.filters[e];return Array.isArray(t)&&t.length>0}return Object.values(this.controller.filters).some((e=>Array.isArray(e)&&e.length>0))}},{key:"_handleSortingChanged",value:function(e){var t=e.detail,i=t.column,o=t.direction;this.controller.sortColumn=o?i:void 0,this.controller.sortDirection=o||void 0}},{key:"_handleRowClick",value:function(e){this.controller.selectedTelegramId=e.detail.id}},{key:"_handleDialogClosed",value:function(){this.controller.selectedTelegramId=null}},{key:"_handlePauseToggle",value:(u=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.controller.togglePause();case 1:return e.a(2)}}),e,this)}))),function(){return u.apply(this,arguments)})},{key:"_handleReload",value:(o=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.controller.reload(this.hass);case 1:return e.a(2)}}),e,this)}))),function(){return o.apply(this,arguments)})},{key:"_retryConnection",value:(i=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.controller.retryConnection(this.hass);case 1:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_handleClearFilters",value:function(){this.controller.clearFilters(this.route)}},{key:"_handleClearRows",value:function(){this.controller.clearTelegrams()}},{key:"_selectNextTelegram",value:function(){var e=this._getFilteredData().filteredTelegrams;this.controller.navigateTelegram(1,e)}},{key:"_selectPreviousTelegram",value:function(){var e=this._getFilteredData().filteredTelegrams;this.controller.navigateTelegram(-1,e)}},{key:"_formatOffsetWithPrecision",value:function(e){return null===e?(0,x.RL)(e):0===Math.round(e/1e3)&&0!==e?(0,x.RL)(e,"microseconds"):(0,x.RL)(e,"milliseconds")}},{key:"_renderTelegramInfoDialog",value:function(e){var t=this._getFilteredData().filteredTelegrams,i=t.findIndex((t=>t.id===e)),o=t[i];return o?(0,h.qy)(L||(L=Z`
      <knx-group-monitor-telegram-info-dialog
        .hass=${0}
        .knx=${0}
        .narrow=${0}
        .telegram=${0}
        .disableNext=${0}
        .disablePrevious=${0}
        @next-telegram=${0}
        @previous-telegram=${0}
        @dialog-closed=${0}
      >
      </knx-group-monitor-telegram-info-dialog>
    `),this.hass,this.knx,this.narrow,o,i+1>=t.length,i<=0,this._selectNextTelegram,this._selectPreviousTelegram,this._handleDialogClosed):h.s6}},{key:"render",value:function(){var e,t,i,o,r=Object.values(this.controller.filters).filter((e=>Array.isArray(e)&&e.length)).length,n=this._getFilteredData(),a=n.filteredTelegrams,l=n.distinctValues;return(0,h.qy)(H||(H=Z`
      <hass-tabs-subpage-data-table
        .hass=${0}
        .narrow=${0}
        .route=${0}
        .tabs=${0}
        main-page
        .columns=${0}
        .noDataText=${0}
        .data=${0}
        .hasFab=${0}
        .searchLabel=${0}
        .localizeFunc=${0}
        id="id"
        .clickable=${0}
        .initialSorting=${0}
        @row-click=${0}
        @sorting-changed=${0}
        has-filters
        .filters=${0}
        @clear-filter=${0}
      >
        <!-- Top header -->
        ${0}
        ${0}
        ${0}

        <!-- Toolbar actions -->
        <div slot="toolbar-icon" class="toolbar-actions">
          <ha-icon-button
            .label=${0}
            .path=${0}
            class=${0}
            @click=${0}
            data-testid="pause-button"
            .title=${0}
          >
          </ha-icon-button>
          <ha-icon-button
            .label=${0}
            .path=${0}
            @click=${0}
            ?disabled=${0}
            data-testid="clean-button"
            .title=${0}
          >
          </ha-icon-button>
          <ha-icon-button
            .label=${0}
            .path=${0}
            @click=${0}
            ?disabled=${0}
            data-testid="reload-button"
            .title=${0}
          >
          </ha-icon-button>
        </div>

        <!-- Filter for Source Address -->
        <knx-list-filter
          data-filter="source"
          slot="filter-pane"
          .hass=${0}
          .knx=${0}
          .data=${0}
          .config=${0}
          .selectedOptions=${0}
          .expanded=${0}
          .narrow=${0}
          .isMobileDevice=${0}
          .filterTitle=${0}
          @selection-changed=${0}
          @expanded-changed=${0}
          @sort-changed=${0}
        ></knx-list-filter>

        <!-- Filter for Destination Address -->
        <knx-list-filter
          data-filter="destination"
          slot="filter-pane"
          .hass=${0}
          .knx=${0}
          .data=${0}
          .config=${0}
          .selectedOptions=${0}
          .expanded=${0}
          .narrow=${0}
          .isMobileDevice=${0}
          .filterTitle=${0}
          @selection-changed=${0}
          @expanded-changed=${0}
          @sort-changed=${0}
        ></knx-list-filter>

        <!-- Filter for Direction -->
        <knx-list-filter
          slot="filter-pane"
          .hass=${0}
          .knx=${0}
          .data=${0}
          .config=${0}
          .selectedOptions=${0}
          .pinSelectedItems=${0}
          .expanded=${0}
          .narrow=${0}
          .isMobileDevice=${0}
          .filterTitle=${0}
          @selection-changed=${0}
          @expanded-changed=${0}
        ></knx-list-filter>

        <!-- Filter for Telegram Type -->
        <knx-list-filter
          slot="filter-pane"
          .hass=${0}
          .knx=${0}
          .data=${0}
          .config=${0}
          .selectedOptions=${0}
          .pinSelectedItems=${0}
          .expanded=${0}
          .narrow=${0}
          .isMobileDevice=${0}
          .filterTitle=${0}
          @selection-changed=${0}
          @expanded-changed=${0}
        ></knx-list-filter>
      </hass-tabs-subpage-data-table>

      <!-- Telegram detail dialog -->
      ${0}
    `),this.hass,this.narrow,this.route,this.tabs,this._columns(this.narrow,!0===this.controller.isProjectLoaded,this.hass.language),this.knx.localize("group_monitor_waiting_message"),a,!1,this.searchLabel,this.knx.localize,!0,{column:this.controller.sortColumn||"timestampIso",direction:this.controller.sortDirection||"desc"},this._handleRowClick,this._handleSortingChanged,r,this._handleClearFilters,this.controller.connectionError?(0,h.qy)(I||(I=Z`
              <ha-alert
                slot="top-header"
                .alertType=${0}
                .title=${0}
              >
                ${0}
                <ha-button slot="action" @click=${0}>
                  ${0}
                </ha-button>
              </ha-alert>
            `),"error",this.knx.localize("group_monitor_connection_error_title"),this.controller.connectionError,this._retryConnection,this.knx.localize("group_monitor_retry_connection")):h.s6,this.controller.isPaused?(0,h.qy)(O||(O=Z`
              <ha-alert
                slot="top-header"
                .alertType=${0}
                .dismissable=${0}
                .title=${0}
              >
                ${0}
                <ha-button slot="action" @click=${0}>
                  ${0}
                </ha-button>
              </ha-alert>
            `),"info",!1,this.knx.localize("group_monitor_paused_title"),this.knx.localize("group_monitor_paused_message"),this._handlePauseToggle,this.knx.localize("group_monitor_resume")):"",!1===this.controller.isProjectLoaded?(0,h.qy)(E||(E=Z`
              <ha-alert
                slot="top-header"
                .alertType=${0}
                .dismissable=${0}
                .title=${0}
              >
                ${0}
              </ha-alert>
            `),"info",!0,this.knx.localize("group_monitor_project_not_loaded_title"),this.knx.localize("group_monitor_project_not_loaded_message")):h.s6,this.controller.isPaused?this.knx.localize("group_monitor_resume"):this.knx.localize("group_monitor_pause"),this.controller.isPaused?"M13,6V18L21.5,12M4,18L12.5,12L4,6V18Z":"M14,19H18V5H14M6,19H10V5H6V19Z",this.controller.isPaused?"active":"",this._handlePauseToggle,this.controller.isPaused?this.knx.localize("group_monitor_resume"):this.knx.localize("group_monitor_pause"),this.knx.localize("group_monitor_clear"),"M15,16H19V18H15V16M15,8H22V10H15V8M15,12H21V14H15V12M3,18A2,2 0 0,0 5,20H11A2,2 0 0,0 13,18V8H3V18M14,5H11L10,4H6L5,5H2V7H14V5Z",this._handleClearRows,0===this.controller.telegrams.length,this.knx.localize("group_monitor_clear"),this.knx.localize("group_monitor_reload"),"M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z",this._handleReload,!this.controller.isReloadEnabled,this.knx.localize("group_monitor_reload"),this.hass,this.knx,Object.values(l.source),this._sourceFilterConfig(this._hasActiveFilters("source"),(null===(e=this.controller.filters.source)||void 0===e?void 0:e.length)||0,null===(t=this.sourceFilter)||void 0===t?void 0:t.sortCriterion,this.hass.language),this.controller.filters.source,"source"===this.controller.expandedFilter,this.narrow,this.isMobileTouchDevice,this.knx.localize("group_monitor_source"),this._handleSourceFilterChange,this._handleSourceFilterExpanded,this._handleFilterSortChanged,this.hass,this.knx,Object.values(l.destination),this._destinationFilterConfig(this._hasActiveFilters("destination"),(null===(i=this.controller.filters.destination)||void 0===i?void 0:i.length)||0,null===(o=this.destinationFilter)||void 0===o?void 0:o.sortCriterion,this.hass.language),this.controller.filters.destination,"destination"===this.controller.expandedFilter,this.narrow,this.isMobileTouchDevice,this.knx.localize("group_monitor_destination"),this._handleDestinationFilterChange,this._handleDestinationFilterExpanded,this._handleFilterSortChanged,this.hass,this.knx,Object.values(l.direction),this._directionFilterConfig(this._hasActiveFilters("direction"),this.hass.language),this.controller.filters.direction,!1,"direction"===this.controller.expandedFilter,this.narrow,this.isMobileTouchDevice,this.knx.localize("group_monitor_direction"),this._handleDirectionFilterChange,this._handleDirectionFilterExpanded,this.hass,this.knx,Object.values(l.telegramtype),this._telegramTypeFilterConfig(this._hasActiveFilters("telegramtype"),this.hass.language),this.controller.filters.telegramtype,!1,"telegramtype"===this.controller.expandedFilter,this.narrow,this.isMobileTouchDevice,this.knx.localize("group_monitor_type"),this._handleTelegramTypeFilterChange,this._handleTelegramTypeFilterExpanded,null!==this.controller.selectedTelegramId?this._renderTelegramInfoDialog(this.controller.selectedTelegramId):h.s6)}}],[{key:"styles",get:function(){return[(0,h.AH)(V||(V=Z`
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
      `))]}}]);var i,o,u,g}(h.WF);(0,u.__decorate)([(0,y.MZ)({type:Object})],q.prototype,"hass",void 0),(0,u.__decorate)([(0,y.MZ)({attribute:!1})],q.prototype,"knx",void 0),(0,u.__decorate)([(0,y.MZ)({type:Boolean,reflect:!0})],q.prototype,"narrow",void 0),(0,u.__decorate)([(0,y.MZ)({type:Object})],q.prototype,"route",void 0),(0,u.__decorate)([(0,y.MZ)({type:Array,reflect:!1})],q.prototype,"tabs",void 0),(0,u.__decorate)([(0,y.P)('knx-list-filter[data-filter="source"]')],q.prototype,"sourceFilter",void 0),(0,u.__decorate)([(0,y.P)('knx-list-filter[data-filter="destination"]')],q.prototype,"destinationFilter",void 0),q=(0,u.__decorate)([(0,y.EM)("knx-group-monitor")],q),o()}catch(j){o(j)}}))},25474:function(e,t,i){i.d(t,{CY:function(){return l},HF:function(){return a},RL:function(){return f},Zc:function(){return n},e4:function(){return r},u_:function(){return g}});i(25276),i(72712),i(34782),i(18111),i(18237),i(2892),i(26099),i(27495),i(38781),i(71761),i(35701),i(68156);var o=i(53289),r={payload:e=>null==e.payload?"":Array.isArray(e.payload)?e.payload.reduce(((e,t)=>e+t.toString(16).padStart(2,"0")),"0x"):e.payload.toString(),valueWithUnit:e=>null==e.value?"":"number"==typeof e.value||"boolean"==typeof e.value||"string"==typeof e.value?e.value.toString()+(e.unit?" "+e.unit:""):(0,o.Bh)(e.value),timeWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString(["en-US"],{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dateWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dptNumber:e=>null==e.dpt_main?"":null==e.dpt_sub?e.dpt_main.toString():e.dpt_main.toString()+"."+e.dpt_sub.toString().padStart(3,"0"),dptNameNumber:e=>{var t=r.dptNumber(e);return null==e.dpt_name?`DPT ${t}`:t?`DPT ${t} ${e.dpt_name}`:e.dpt_name}},n=e=>e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),a=e=>e.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),l=e=>{var t=new Date(e),i=e.match(/\.(\d{6})/),o=i?i[1]:"000000";return t.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+t.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit"})+"."+o},s=1e3,d=1e3,c=60*d,u=60*c,h=2,p=3;function g(e){var t=e.indexOf(".");if(-1===t)return 1e3*Date.parse(e);var i=e.indexOf("Z",t);-1===i&&-1===(i=e.indexOf("+",t))&&(i=e.indexOf("-",t)),-1===i&&(i=e.length);var o=e.slice(0,t)+e.slice(i),r=Date.parse(o),n=e.slice(t+1,i);return n.length<6?n=n.padEnd(6,"0"):n.length>6&&(n=n.slice(0,6)),1e3*r+Number(n)}function f(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"milliseconds";if(null==e)return"—";var i=e<0?"-":"",o=Math.abs(e),r="milliseconds"===t?Math.round(o/s):Math.floor(o/s),n="microseconds"===t?o%s:0,a=Math.floor(r/u),l=Math.floor(r%u/c),g=Math.floor(r%c/d),f=r%d,v=e=>e.toString().padStart(h,"0"),m=e=>e.toString().padStart(p,"0"),_="microseconds"===t?`.${m(f)}${m(n)}`:`.${m(f)}`,b=`${v(l)}:${v(g)}`;return`${i}${a>0?`${v(a)}:${b}`:b}${_}`}}}]);
//# sourceMappingURL=8024.447249d8c5abd076.js.map