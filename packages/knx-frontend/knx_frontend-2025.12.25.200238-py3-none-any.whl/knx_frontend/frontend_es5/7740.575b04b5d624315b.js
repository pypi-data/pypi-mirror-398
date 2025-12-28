"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7740"],{10253:function(e,t,a){a.a(e,(async function(e,r){try{a.d(t,{P:function(){return c}});a(74423),a(25276);var o=a(22),n=a(58109),i=a(81793),s=a(44740),l=e([o]);o=(l.then?(await l)():l)[0];var c=e=>e.first_weekday===i.zt.language?"weekInfo"in Intl.Locale.prototype?new Intl.Locale(e.language).weekInfo.firstDay%7:(0,n.S)(e.language)%7:s.Z.includes(e.first_weekday)?s.Z.indexOf(e.first_weekday):1;r()}catch(d){r(d)}}))},77646:function(e,t,a){a.a(e,(async function(e,r){try{a.d(t,{K:function(){return c}});var o=a(22),n=a(22786),i=a(97518),s=e([o,i]);[o,i]=s.then?(await s)():s;var l=(0,n.A)((e=>new Intl.RelativeTimeFormat(e.language,{numeric:"auto"}))),c=function(e,t,a){var r=!(arguments.length>3&&void 0!==arguments[3])||arguments[3],o=(0,i.x)(e,a,t);return r?l(t).format(o.value,o.unit):Intl.NumberFormat(t.language,{style:"unit",unit:o.unit,unitDisplay:"long"}).format(Math.abs(o.value))};r()}catch(d){r(d)}}))},44740:function(e,t,a){a.d(t,{Z:function(){return r}});var r=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"]},97518:function(e,t,a){a.a(e,(async function(e,r){try{a.d(t,{x:function(){return g}});var o=a(6946),n=a(52640),i=a(56232),s=a(10253),l=e([s]);s=(l.then?(await l)():l)[0];var c=1e3,d=60,u=60*d;function g(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:Date.now(),a=arguments.length>2?arguments[2]:void 0,r=arguments.length>3&&void 0!==arguments[3]?arguments[3]:{},l=Object.assign(Object.assign({},p),r||{}),h=(+e-+t)/c;if(Math.abs(h)<l.second)return{value:Math.round(h),unit:"second"};var g=h/d;if(Math.abs(g)<l.minute)return{value:Math.round(g),unit:"minute"};var v=h/u;if(Math.abs(v)<l.hour)return{value:Math.round(v),unit:"hour"};var b=new Date(e),f=new Date(t);b.setHours(0,0,0,0),f.setHours(0,0,0,0);var m=(0,o.c)(b,f);if(0===m)return{value:Math.round(v),unit:"hour"};if(Math.abs(m)<l.day)return{value:m,unit:"day"};var y=(0,s.P)(a),_=(0,n.k)(b,{weekStartsOn:y}),w=(0,n.k)(f,{weekStartsOn:y}),k=(0,i.I)(_,w);if(0===k)return{value:m,unit:"day"};if(Math.abs(k)<l.week)return{value:k,unit:"week"};var x=b.getFullYear()-f.getFullYear(),A=12*x+b.getMonth()-f.getMonth();return 0===A?{value:k,unit:"week"}:Math.abs(A)<l.month||0===x?{value:A,unit:"month"}:{value:Math.round(x),unit:"year"}}var p={second:59,minute:59,hour:22,day:5,week:4,month:11};r()}catch(h){r(h)}}))},17963:function(e,t,a){a.r(t);var r,o,n,i,s=a(44734),l=a(56038),c=a(69683),d=a(6454),u=(a(28706),a(62826)),p=a(96196),h=a(77845),g=a(94333),v=a(92542),b=(a(60733),a(60961),e=>e),f={info:"M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",warning:"M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",error:"M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z",success:"M20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4C12.76,4 13.5,4.11 14.2,4.31L15.77,2.74C14.61,2.26 13.34,2 12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"},m=function(e){function t(){var e;(0,s.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,c.A)(this,t,[].concat(r))).title="",e.alertType="info",e.dismissable=!1,e.narrow=!1,e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"render",value:function(){return(0,p.qy)(r||(r=b`
      <div
        class="issue-type ${0}"
        role="alert"
      >
        <div class="icon ${0}">
          <slot name="icon">
            <ha-svg-icon .path=${0}></ha-svg-icon>
          </slot>
        </div>
        <div class=${0}>
          <div class="main-content">
            ${0}
            <slot></slot>
          </div>
          <div class="action">
            <slot name="action">
              ${0}
            </slot>
          </div>
        </div>
      </div>
    `),(0,g.H)({[this.alertType]:!0}),this.title?"":"no-title",f[this.alertType],(0,g.H)({content:!0,narrow:this.narrow}),this.title?(0,p.qy)(o||(o=b`<div class="title">${0}</div>`),this.title):p.s6,this.dismissable?(0,p.qy)(n||(n=b`<ha-icon-button
                    @click=${0}
                    label="Dismiss alert"
                    .path=${0}
                  ></ha-icon-button>`),this._dismissClicked,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"):p.s6)}},{key:"_dismissClicked",value:function(){(0,v.r)(this,"alert-dismissed-clicked")}}])}(p.WF);m.styles=(0,p.AH)(i||(i=b`
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
  `)),(0,u.__decorate)([(0,h.MZ)()],m.prototype,"title",void 0),(0,u.__decorate)([(0,h.MZ)({attribute:"alert-type"})],m.prototype,"alertType",void 0),(0,u.__decorate)([(0,h.MZ)({type:Boolean})],m.prototype,"dismissable",void 0),(0,u.__decorate)([(0,h.MZ)({type:Boolean})],m.prototype,"narrow",void 0),m=(0,u.__decorate)([(0,h.EM)("ha-alert")],m)},95379:function(e,t,a){var r,o,n,i=a(44734),s=a(56038),l=a(69683),c=a(6454),d=(a(28706),a(62826)),u=a(96196),p=a(77845),h=e=>e,g=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,l.A)(this,t,[].concat(r))).raised=!1,e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,u.qy)(r||(r=h`
      ${0}
      <slot></slot>
    `),this.header?(0,u.qy)(o||(o=h`<h1 class="card-header">${0}</h1>`),this.header):u.s6)}}])}(u.WF);g.styles=(0,u.AH)(n||(n=h`
    :host {
      background: var(
        --ha-card-background,
        var(--card-background-color, white)
      );
      -webkit-backdrop-filter: var(--ha-card-backdrop-filter, none);
      backdrop-filter: var(--ha-card-backdrop-filter, none);
      box-shadow: var(--ha-card-box-shadow, none);
      box-sizing: border-box;
      border-radius: var(--ha-card-border-radius, var(--ha-border-radius-lg));
      border-width: var(--ha-card-border-width, 1px);
      border-style: solid;
      border-color: var(--ha-card-border-color, var(--divider-color, #e0e0e0));
      color: var(--primary-text-color);
      display: block;
      transition: all 0.3s ease-out;
      position: relative;
    }

    :host([raised]) {
      border: none;
      box-shadow: var(
        --ha-card-box-shadow,
        0px 2px 1px -1px rgba(0, 0, 0, 0.2),
        0px 1px 1px 0px rgba(0, 0, 0, 0.14),
        0px 1px 3px 0px rgba(0, 0, 0, 0.12)
      );
    }

    .card-header,
    :host ::slotted(.card-header) {
      color: var(--ha-card-header-color, var(--primary-text-color));
      font-family: var(--ha-card-header-font-family, inherit);
      font-size: var(--ha-card-header-font-size, var(--ha-font-size-2xl));
      letter-spacing: -0.012em;
      line-height: var(--ha-line-height-expanded);
      padding: var(--ha-space-3) var(--ha-space-4) var(--ha-space-4);
      display: block;
      margin-block-start: var(--ha-space-0);
      margin-block-end: var(--ha-space-0);
      font-weight: var(--ha-font-weight-normal);
    }

    :host ::slotted(.card-content:not(:first-child)),
    slot:not(:first-child)::slotted(.card-content) {
      padding-top: var(--ha-space-0);
      margin-top: calc(var(--ha-space-2) * -1);
    }

    :host ::slotted(.card-content) {
      padding: var(--ha-space-4);
    }

    :host ::slotted(.card-actions) {
      border-top: 1px solid var(--divider-color, #e8e8e8);
      padding: var(--ha-space-2);
    }
  `)),(0,d.__decorate)([(0,p.MZ)()],g.prototype,"header",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],g.prototype,"raised",void 0),g=(0,d.__decorate)([(0,p.EM)("ha-card")],g)},53623:function(e,t,a){a.a(e,(async function(e,r){try{a.r(t),a.d(t,{HaIconOverflowMenu:function(){return A}});var o=a(44734),n=a(56038),i=a(69683),s=a(6454),l=(a(28706),a(62062),a(18111),a(61701),a(26099),a(62826)),c=a(96196),d=a(77845),u=a(94333),p=a(39396),h=(a(63419),a(60733),a(60961),a(88422)),g=(a(99892),a(32072),e([h]));h=(g.then?(await g)():g)[0];var v,b,f,m,y,_,w,k,x=e=>e,A=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,r=new Array(a),n=0;n<a;n++)r[n]=arguments[n];return(e=(0,i.A)(this,t,[].concat(r))).items=[],e.narrow=!1,e}return(0,s.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return 0===this.items.length?c.s6:(0,c.qy)(v||(v=x`
      ${0}
    `),this.narrow?(0,c.qy)(b||(b=x` <!-- Collapsed representation for small screens -->
            <ha-md-button-menu
              @click=${0}
              positioning="popover"
            >
              <ha-icon-button
                .label=${0}
                .path=${0}
                slot="trigger"
              ></ha-icon-button>

              ${0}
            </ha-md-button-menu>`),this._handleIconOverflowMenuOpened,this.hass.localize("ui.common.overflow_menu"),"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this.items.map((e=>e.divider?(0,c.qy)(f||(f=x`<ha-md-divider
                      role="separator"
                      tabindex="-1"
                    ></ha-md-divider>`)):(0,c.qy)(m||(m=x`<ha-md-menu-item
                      ?disabled=${0}
                      .clickAction=${0}
                      class=${0}
                    >
                      <ha-svg-icon
                        slot="start"
                        class=${0}
                        .path=${0}
                      ></ha-svg-icon>
                      ${0}
                    </ha-md-menu-item>`),e.disabled,e.action,(0,u.H)({warning:Boolean(e.warning)}),(0,u.H)({warning:Boolean(e.warning)}),e.path,e.label)))):(0,c.qy)(y||(y=x`
            <!-- Icon representation for big screens -->
            ${0}
          `),this.items.map((e=>{var t;return e.narrowOnly?c.s6:e.divider?(0,c.qy)(_||(_=x`<div role="separator"></div>`)):(0,c.qy)(w||(w=x`<ha-tooltip
                        .disabled=${0}
                        .for="icon-button-${0}"
                        >${0} </ha-tooltip
                      ><ha-icon-button
                        .id="icon-button-${0}"
                        @click=${0}
                        .label=${0}
                        .path=${0}
                        ?disabled=${0}
                      ></ha-icon-button> `),!e.tooltip,e.label,null!==(t=e.tooltip)&&void 0!==t?t:"",e.label,e.action,e.label,e.path,e.disabled)}))))}},{key:"_handleIconOverflowMenuOpened",value:function(e){e.stopPropagation()}}],[{key:"styles",get:function(){return[p.RF,(0,c.AH)(k||(k=x`
        :host {
          display: flex;
          justify-content: flex-end;
          cursor: initial;
        }
        div[role="separator"] {
          border-right: 1px solid var(--divider-color);
          width: 1px;
        }
      `))]}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({type:Array})],A.prototype,"items",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],A.prototype,"narrow",void 0),A=(0,l.__decorate)([(0,d.EM)("ha-icon-overflow-menu")],A),r()}catch($){r($)}}))},88422:function(e,t,a){a.a(e,(async function(e,t){try{var r=a(44734),o=a(56038),n=a(69683),i=a(6454),s=(a(28706),a(2892),a(62826)),l=a(52630),c=a(96196),d=a(77845),u=e([l]);l=(u.then?(await u)():u)[0];var p,h=e=>e,g=function(e){function t(){var e;(0,r.A)(this,t);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(e=(0,n.A)(this,t,[].concat(o))).showDelay=150,e.hideDelay=150,e}return(0,i.A)(t,e),(0,o.A)(t,null,[{key:"styles",get:function(){return[l.A.styles,(0,c.AH)(p||(p=h`
        :host {
          --wa-tooltip-background-color: var(--secondary-background-color);
          --wa-tooltip-content-color: var(--primary-text-color);
          --wa-tooltip-font-family: var(
            --ha-tooltip-font-family,
            var(--ha-font-family-body)
          );
          --wa-tooltip-font-size: var(
            --ha-tooltip-font-size,
            var(--ha-font-size-s)
          );
          --wa-tooltip-font-weight: var(
            --ha-tooltip-font-weight,
            var(--ha-font-weight-normal)
          );
          --wa-tooltip-line-height: var(
            --ha-tooltip-line-height,
            var(--ha-line-height-condensed)
          );
          --wa-tooltip-padding: 8px;
          --wa-tooltip-border-radius: var(
            --ha-tooltip-border-radius,
            var(--ha-border-radius-sm)
          );
          --wa-tooltip-arrow-size: var(--ha-tooltip-arrow-size, 8px);
          --wa-z-index-tooltip: var(--ha-tooltip-z-index, 1000);
        }
      `))]}}])}(l.A);(0,s.__decorate)([(0,d.MZ)({attribute:"show-delay",type:Number})],g.prototype,"showDelay",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:"hide-delay",type:Number})],g.prototype,"hideDelay",void 0),g=(0,s.__decorate)([(0,d.EM)("ha-tooltip")],g),t()}catch(v){t(v)}}))},48680:function(e,t,a){var r,o,n,i,s,l,c=a(78261),d=a(44734),u=a(56038),p=a(69683),h=a(6454),g=a(25460),v=(a(28706),a(62062),a(72712),a(18111),a(7588),a(61701),a(18237),a(5506),a(26099),a(16034),a(23500),a(62826)),b=a(96196),f=a(77845),m=a(94333),y=a(92542),_=a(78577),w=e=>e,k=new _.Q("knx-project-tree-view"),x=function(e){function t(){var e;(0,d.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,p.A)(this,t,[].concat(r))).multiselect=!1,e._selectableRanges={},e}return(0,h.A)(t,e),(0,u.A)(t,[{key:"connectedCallback",value:function(){(0,g.A)(t,"connectedCallback",this,3)([]);var e=t=>{Object.entries(t).forEach((t=>{var a=(0,c.A)(t,2),r=a[0],o=a[1];o.group_addresses.length>0&&(this._selectableRanges[r]={selected:!1,groupAddresses:o.group_addresses}),e(o.group_ranges)}))};e(this.data.group_ranges),k.debug("ranges",this._selectableRanges)}},{key:"render",value:function(){return(0,b.qy)(r||(r=w`<div class="ha-tree-view">${0}</div>`),this._recurseData(this.data.group_ranges))}},{key:"_recurseData",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0,a=Object.entries(e).map((e=>{var a=(0,c.A)(e,2),r=a[0],s=a[1],l=Object.keys(s.group_ranges).length>0;if(!(l||s.group_addresses.length>0))return b.s6;var d=r in this._selectableRanges,u=!!d&&this._selectableRanges[r].selected,p={"range-item":!0,"root-range":0===t,"sub-range":t>0,selectable:d,"selected-range":u,"non-selected-range":d&&!u},h=(0,b.qy)(o||(o=w`<div
        class=${0}
        toggle-range=${0}
        @click=${0}
      >
        <span class="range-key">${0}</span>
        <span class="range-text">${0}</span>
      </div>`),(0,m.H)(p),d?r:b.s6,d?this.multiselect?this._selectionChangedMulti:this._selectionChangedSingle:b.s6,r,s.name);if(l){var g={"root-group":0===t,"sub-group":0!==t};return(0,b.qy)(n||(n=w`<div class=${0}>
          ${0} ${0}
        </div>`),(0,m.H)(g),h,this._recurseData(s.group_ranges,t+1))}return(0,b.qy)(i||(i=w`${0}`),h)}));return(0,b.qy)(s||(s=w`${0}`),a)}},{key:"_selectionChangedMulti",value:function(e){var t=e.target.getAttribute("toggle-range");this._selectableRanges[t].selected=!this._selectableRanges[t].selected,this._selectionUpdate(),this.requestUpdate()}},{key:"_selectionChangedSingle",value:function(e){var t=e.target.getAttribute("toggle-range"),a=this._selectableRanges[t].selected;Object.values(this._selectableRanges).forEach((e=>{e.selected=!1})),this._selectableRanges[t].selected=!a,this._selectionUpdate(),this.requestUpdate()}},{key:"_selectionUpdate",value:function(){var e=Object.values(this._selectableRanges).reduce(((e,t)=>t.selected?e.concat(t.groupAddresses):e),[]);k.debug("selection changed",e),(0,y.r)(this,"knx-group-range-selection-changed",{groupAddresses:e})}}])}(b.WF);x.styles=(0,b.AH)(l||(l=w`
    :host {
      margin: 0;
      height: 100%;
      overflow-y: scroll;
      overflow-x: hidden;
      background-color: var(--card-background-color);
    }

    .ha-tree-view {
      cursor: default;
    }

    .root-group {
      margin-bottom: 8px;
    }

    .root-group > * {
      padding-top: 5px;
      padding-bottom: 5px;
    }

    .range-item {
      display: block;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      font-size: 0.875rem;
    }

    .range-item > * {
      vertical-align: middle;
      pointer-events: none;
    }

    .range-key {
      color: var(--text-primary-color);
      font-size: 0.75rem;
      font-weight: 700;
      background-color: var(--label-badge-grey);
      border-radius: 4px;
      padding: 1px 4px;
      margin-right: 2px;
    }

    .root-range {
      padding-left: 8px;
      font-weight: 500;
      background-color: var(--secondary-background-color);

      & .range-key {
        color: var(--primary-text-color);
        background-color: var(--card-background-color);
      }
    }

    .sub-range {
      padding-left: 13px;
    }

    .selectable {
      cursor: pointer;
    }

    .selectable:hover {
      background-color: rgba(var(--rgb-primary-text-color), 0.04);
    }

    .selected-range {
      background-color: rgba(var(--rgb-primary-color), 0.12);

      & .range-key {
        background-color: var(--primary-color);
      }
    }

    .selected-range:hover {
      background-color: rgba(var(--rgb-primary-color), 0.07);
    }

    .non-selected-range {
      background-color: var(--card-background-color);
    }
  `)),(0,v.__decorate)([(0,f.MZ)({attribute:!1})],x.prototype,"data",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:!1})],x.prototype,"multiselect",void 0),(0,v.__decorate)([(0,f.wk)()],x.prototype,"_selectableRanges",void 0),x=(0,v.__decorate)([(0,f.EM)("knx-project-tree-view")],x)},19337:function(e,t,a){a.d(t,{$k:function(){return u},Ah:function(){return s},HG:function(){return i},Vt:function(){return d},Yb:function(){return c},_O:function(){return p},oJ:function(){return h}});var r=a(94741),o=a(78261),n=(a(28706),a(2008),a(74423),a(62062),a(44114),a(72712),a(18111),a(22489),a(7588),a(61701),a(18237),a(13579),a(5506),a(26099),a(16034),a(38781),a(68156),a(42762),a(23500),a(22786)),i=(e,t)=>t.some((t=>e.main===t.main&&(!t.sub||e.sub===t.sub))),s=(e,t)=>{var a=((e,t)=>Object.entries(e.group_addresses).reduce(((e,a)=>{var r=(0,o.A)(a,2),n=r[0],s=r[1];return s.dpt&&i(s.dpt,t)&&(e[n]=s),e}),{}))(e,t);return Object.entries(e.communication_objects).reduce(((e,t)=>{var r=(0,o.A)(t,2),n=r[0],i=r[1];return i.group_address_links.some((e=>e in a))&&(e[n]=i),e}),{})};function l(e,t){var a=[];return e.forEach((e=>{"knx_group_address"!==e.type?"schema"in e&&a.push.apply(a,(0,r.A)(l(e.schema,t))):e.options.validDPTs?a.push.apply(a,(0,r.A)(e.options.validDPTs)):e.options.dptSelect?a.push.apply(a,(0,r.A)(e.options.dptSelect.map((e=>e.dpt)))):e.options.dptClasses&&a.push.apply(a,(0,r.A)(Object.values(t).filter((t=>e.options.dptClasses.includes(t.dpt_class))).map((e=>({main:e.main,sub:e.sub})))))})),a}var c=(0,n.A)(((e,t)=>l(e,t).reduce(((e,t)=>e.some((e=>{return r=t,(a=e).main===r.main&&a.sub===r.sub;var a,r}))?e:e.concat([t])),[]))),d=e=>null==e?"":e.main+(null!=e.sub?"."+e.sub.toString().padStart(3,"0"):""),u=e=>{if(!e)return null;var t=e.trim().split(".");if(0===t.length||t.length>2)return null;var a=Number.parseInt(t[0],10);if(Number.isNaN(a))return null;if(1===t.length)return{main:a,sub:null};var r=Number.parseInt(t[1],10);return Number.isNaN(r)?null:{main:a,sub:r}},p=(e,t)=>{var a,r;return e.main!==t.main?e.main-t.main:(null!==(a=e.sub)&&void 0!==a?a:-1)-(null!==(r=t.sub)&&void 0!==r?r:-1)},h=(e,t,a)=>{var r=a[d(e)];return!!r&&t.includes(r.dpt_class)}},25474:function(e,t,a){a.d(t,{CY:function(){return s},HF:function(){return i},RL:function(){return v},Zc:function(){return n},e4:function(){return o},u_:function(){return g}});a(25276),a(72712),a(34782),a(18111),a(18237),a(2892),a(26099),a(27495),a(38781),a(71761),a(35701),a(68156);var r=a(53289),o={payload:e=>null==e.payload?"":Array.isArray(e.payload)?e.payload.reduce(((e,t)=>e+t.toString(16).padStart(2,"0")),"0x"):e.payload.toString(),valueWithUnit:e=>null==e.value?"":"number"==typeof e.value||"boolean"==typeof e.value||"string"==typeof e.value?e.value.toString()+(e.unit?" "+e.unit:""):(0,r.Bh)(e.value),timeWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString(["en-US"],{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dateWithMilliseconds:e=>new Date(e.timestamp).toLocaleTimeString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),dptNumber:e=>null==e.dpt_main?"":null==e.dpt_sub?e.dpt_main.toString():e.dpt_main.toString()+"."+e.dpt_sub.toString().padStart(3,"0"),dptNameNumber:e=>{var t=o.dptNumber(e);return null==e.dpt_name?`DPT ${t}`:t?`DPT ${t} ${e.dpt_name}`:e.dpt_name}},n=e=>e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),i=e=>e.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+e.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit",fractionalSecondDigits:3}),s=e=>{var t=new Date(e),a=e.match(/\.(\d{6})/),r=a?a[1]:"000000";return t.toLocaleDateString(void 0,{year:"numeric",month:"2-digit",day:"2-digit"})+", "+t.toLocaleTimeString(void 0,{hour12:!1,hour:"2-digit",minute:"2-digit",second:"2-digit"})+"."+r},l=1e3,c=1e3,d=60*c,u=60*d,p=2,h=3;function g(e){var t=e.indexOf(".");if(-1===t)return 1e3*Date.parse(e);var a=e.indexOf("Z",t);-1===a&&-1===(a=e.indexOf("+",t))&&(a=e.indexOf("-",t)),-1===a&&(a=e.length);var r=e.slice(0,t)+e.slice(a),o=Date.parse(r),n=e.slice(t+1,a);return n.length<6?n=n.padEnd(6,"0"):n.length>6&&(n=n.slice(0,6)),1e3*o+Number(n)}function v(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"milliseconds";if(null==e)return"—";var a=e<0?"-":"",r=Math.abs(e),o="milliseconds"===t?Math.round(r/l):Math.floor(r/l),n="microseconds"===t?r%l:0,i=Math.floor(o/u),s=Math.floor(o%u/d),g=Math.floor(o%d/c),v=o%c,b=e=>e.toString().padStart(p,"0"),f=e=>e.toString().padStart(h,"0"),m="microseconds"===t?`.${f(v)}${f(n)}`:`.${f(v)}`,y=`${b(s)}:${b(g)}`;return`${a}${i>0?`${b(i)}:${y}`:y}${m}`}},29399:function(e,t,a){a.a(e,(async function(e,r){try{a.r(t),a.d(t,{KNXProjectView:function(){return U}});var o=a(61397),n=a(50264),i=a(44734),s=a(56038),l=a(75864),c=a(69683),d=a(6454),u=a(25460),p=(a(28706),a(2008),a(62062),a(44114),a(26910),a(18111),a(22489),a(61701),a(26099),a(16034),a(38781),a(68156),a(62826)),h=a(96196),g=a(77845),v=a(89302),b=a(22786),f=a(5871),m=a(54393),y=(a(84884),a(17963),a(95379),a(60733),a(53623)),_=(a(37445),a(77646)),w=(a(48680),a(87770)),k=a(19337),x=a(65294),A=a(78577),$=a(25474),M=e([m,y,_]);[m,y,_]=M.then?(await M)():M;var H,j,S,V,L,z,D,q,C,Z,O,R,T,N,E,I=e=>e,W="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",F=new A.Q("knx-project-view"),U=function(e){function t(){var e,a;(0,i.A)(this,t);for(var r=arguments.length,s=new Array(r),d=0;d<r;d++)s[d]=arguments[d];return(e=(0,c.A)(this,t,[].concat(s))).rangeSelectorHidden=!0,e._visibleGroupAddresses=[],e._groupRangeAvailable=!1,e._lastTelegrams={},e._projectLoadTask=new v.YZ((0,l.A)(e),{args:()=>[],task:(a=(0,n.A)((0,o.A)().m((function t(){return(0,o.A)().w((function(t){for(;;)switch(t.n){case 0:if(!e.knx.projectInfo||e.knx.projectData){t.n=1;break}return t.n=1,e.knx.loadProject();case 1:e._isGroupRangeAvailable();case 2:return t.a(2)}}),t)}))),function(){return a.apply(this,arguments)})}),e._columns=(0,b.A)(((t,a)=>({address:{filterable:!0,sortable:!0,title:e.knx.localize("project_view_table_address"),flex:1,minWidth:"100px",direction:"asc"},name:{filterable:!0,sortable:!0,title:e.knx.localize("project_view_table_name"),flex:3},dpt:{sortable:!0,filterable:!0,title:e.knx.localize("project_view_table_dpt"),flex:1,minWidth:"82px",template:e=>e.dpt?(0,h.qy)(H||(H=I`<span style="display:inline-block;width:24px;text-align:right;"
                  >${0}</span
                >${0} `),e.dpt.main,e.dpt.sub?"."+e.dpt.sub.toString().padStart(3,"0"):""):""},lastValue:{filterable:!0,title:e.knx.localize("project_view_table_last_value"),flex:2,template:t=>{var a=e._lastTelegrams[t.address];if(!a)return"";var r=$.e4.payload(a);return null==a.value?(0,h.qy)(j||(j=I`<code>${0}</code>`),r):(0,h.qy)(S||(S=I`<div title=${0}>
            ${0}
          </div>`),r,$.e4.valueWithUnit(e._lastTelegrams[t.address]))}},updated:{title:e.knx.localize("project_view_table_updated"),flex:1,showNarrow:!1,template:t=>{var a=e._lastTelegrams[t.address];if(!a)return"";var r=`${$.e4.dateWithMilliseconds(a)}\n\n${a.source} ${a.source_name}`;return(0,h.qy)(V||(V=I`<div title=${0}>
            ${0}
          </div>`),r,(0,_.K)(new Date(a.timestamp),e.hass.locale))}},actions:{title:"",minWidth:"72px",type:"overflow-menu",template:t=>e._groupAddressMenu(t)}}))),e._getRows=(0,b.A)(((e,t)=>e.length?e.map((e=>t[e])).filter((e=>!!e)).sort(((e,t)=>e.raw_address-t.raw_address)):Object.values(t))),e}return(0,d.A)(t,e),(0,s.A)(t,[{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._subscribed&&(this._subscribed(),this._subscribed=void 0)}},{key:"firstUpdated",value:(a=(0,n.A)((0,o.A)().m((function e(){return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:return(0,x.ke)(this.hass).then((e=>{this._lastTelegrams=e})).catch((e=>{F.error("getGroupTelegrams",e),(0,f.o)("/knx/error",{replace:!0,data:e})})),e.n=1,(0,x.EE)(this.hass,(e=>{this.telegram_callback(e)}));case 1:this._subscribed=e.v;case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"_isGroupRangeAvailable",value:function(){var e,t,a=null!==(e=null===(t=this.knx.projectData)||void 0===t?void 0:t.info.xknxproject_version)&&void 0!==e?e:"0.0.0";F.debug("project version: "+a),this._groupRangeAvailable=(0,w.U)(a,"3.3.0",">=")}},{key:"telegram_callback",value:function(e){this._lastTelegrams=Object.assign(Object.assign({},this._lastTelegrams),{},{[e.destination]:e})}},{key:"_groupAddressMenu",value:function(e){var t=[];if(t.push({path:"M18 7C16.9 7 16 7.9 16 9V15C16 16.1 16.9 17 18 17H20C21.1 17 22 16.1 22 15V11H20V15H18V9H22V7H18M2 7V17H8V15H4V7H2M11 7C9.9 7 9 7.9 9 9V15C9 16.1 9.9 17 11 17H13C14.1 17 15 16.1 15 15V9C15 7.9 14.1 7 13 7H11M11 9H13V15H11V9Z",label:this.knx.localize("project_view_menu_view_telegrams"),action:()=>{(0,f.o)(`/knx/group_monitor?destination=${e.address}`)}}),e.dpt)if(1===e.dpt.main)t.push({path:W,label:this.knx.localize("project_view_menu_create_binary_sensor"),action:()=>{(0,f.o)("/knx/entities/create/binary_sensor?knx.ga_sensor.state="+e.address)}});else if((0,k.oJ)(e.dpt,["numeric","string"],this.knx.dptMetadata)){var a;t.push({path:W,label:null!==(a=this.knx.localize("project_view_menu_create_sensor"))&&void 0!==a?a:"Create Sensor",action:()=>{var t=e.dpt?`${e.dpt.main}${null!==e.dpt.sub?"."+e.dpt.sub.toString().padStart(3,"0"):""}`:"";(0,f.o)(`/knx/entities/create/sensor?knx.ga_sensor.state=${e.address}`+(t?`&knx.ga_sensor.dpt=${t}`:""))}})}return(0,h.qy)(L||(L=I`
      <ha-icon-overflow-menu .hass=${0} narrow .items=${0}> </ha-icon-overflow-menu>
    `),this.hass,t)}},{key:"_visibleAddressesChanged",value:function(e){this._visibleGroupAddresses=e.detail.groupAddresses}},{key:"render",value:function(){return this.hass?(0,h.qy)(D||(D=I` <hass-tabs-subpage
      .hass=${0}
      .narrow=${0}
      .route=${0}
      .tabs=${0}
      .localizeFunc=${0}
      main-page
    >
      ${0}
    </hass-tabs-subpage>`),this.hass,this.narrow,this.route,this.tabs,this.knx.localize,this._projectLoadTask.render({initial:()=>(0,h.qy)(q||(q=I`
          <hass-loading-screen .message=${0}></hass-loading-screen>
        `),"Waiting to fetch project data."),pending:()=>(0,h.qy)(C||(C=I`
          <hass-loading-screen .message=${0}></hass-loading-screen>
        `),"Loading KNX project data."),error:e=>(F.error("Error loading KNX project",e),(0,h.qy)(Z||(Z=I`<ha-alert alert-type="error">"Error loading KNX project"</ha-alert>`))),complete:()=>this.renderMain()})):(0,h.qy)(z||(z=I` <hass-loading-screen></hass-loading-screen> `))}},{key:"renderMain",value:function(){var e=this._getRows(this._visibleGroupAddresses,this.knx.projectData.group_addresses);return this.knx.projectData?(0,h.qy)(O||(O=I`${0}
          <div class="sections">
            ${0}
            <ha-data-table
              class="ga-table"
              .hass=${0}
              .columns=${0}
              .data=${0}
              .hasFab=${0}
              .searchLabel=${0}
              .clickable=${0}
            ></ha-data-table>
          </div>`),this.narrow&&this._groupRangeAvailable?(0,h.qy)(R||(R=I`<ha-icon-button
                slot="toolbar-icon"
                .label=${0}
                .path=${0}
                @click=${0}
              ></ha-icon-button>`),this.hass.localize("ui.components.related-filter-menu.filter"),"M6,13H18V11H6M3,6V8H21V6M10,18H14V16H10V18Z",this._toggleRangeSelector):h.s6,this._groupRangeAvailable?(0,h.qy)(T||(T=I`
                  <knx-project-tree-view
                    .data=${0}
                    @knx-group-range-selection-changed=${0}
                  ></knx-project-tree-view>
                `),this.knx.projectData,this._visibleAddressesChanged):h.s6,this.hass,this._columns(this.narrow,this.hass.language),e,!1,this.hass.localize("ui.components.data-table.search"),!1):(0,h.qy)(N||(N=I` <ha-card .header=${0}>
          <div class="card-content">
            <p>${0}</p>
          </div>
        </ha-card>`),this.knx.localize("attention"),this.knx.localize("project_view_upload"))}},{key:"_toggleRangeSelector",value:function(){this.rangeSelectorHidden=!this.rangeSelectorHidden}}]);var a}(h.WF);U.styles=(0,h.AH)(E||(E=I`
    hass-loading-screen {
      --app-header-background-color: var(--sidebar-background-color);
      --app-header-text-color: var(--sidebar-text-color);
    }
    .sections {
      display: flex;
      flex-direction: row;
      height: 100%;
    }

    :host([narrow]) knx-project-tree-view {
      position: absolute;
      max-width: calc(100% - 60px); /* 100% -> max 871px before not narrow */
      z-index: 1;
      right: 0;
      transition: 0.5s;
      border-left: 1px solid var(--divider-color);
    }

    :host([narrow][range-selector-hidden]) knx-project-tree-view {
      width: 0;
    }

    :host(:not([narrow])) knx-project-tree-view {
      max-width: 255px; /* min 616px - 816px for tree-view + ga-table (depending on side menu) */
    }

    .ga-table {
      flex: 1;
    }
  `)),(0,p.__decorate)([(0,g.MZ)({type:Object})],U.prototype,"hass",void 0),(0,p.__decorate)([(0,g.MZ)({attribute:!1})],U.prototype,"knx",void 0),(0,p.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0})],U.prototype,"narrow",void 0),(0,p.__decorate)([(0,g.MZ)({type:Object})],U.prototype,"route",void 0),(0,p.__decorate)([(0,g.MZ)({type:Array,reflect:!1})],U.prototype,"tabs",void 0),(0,p.__decorate)([(0,g.MZ)({type:Boolean,reflect:!0,attribute:"range-selector-hidden"})],U.prototype,"rangeSelectorHidden",void 0),(0,p.__decorate)([(0,g.wk)()],U.prototype,"_visibleGroupAddresses",void 0),(0,p.__decorate)([(0,g.wk)()],U.prototype,"_groupRangeAvailable",void 0),(0,p.__decorate)([(0,g.wk)()],U.prototype,"_subscribed",void 0),(0,p.__decorate)([(0,g.wk)()],U.prototype,"_lastTelegrams",void 0),U=(0,p.__decorate)([(0,g.EM)("knx-project-view")],U),r()}catch(B){r(B)}}))}}]);
//# sourceMappingURL=7740.575b04b5d624315b.js.map