"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["9341"],{38852:function(e,t,i){i.d(t,{b:function(){return s}});var a=i(31432),s=(i(23792),i(36033),i(26099),i(84864),i(57465),i(27495),i(69479),i(38781),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(62953),(e,t)=>{if(e===t)return!0;if(e&&t&&"object"==typeof e&&"object"==typeof t){if(e.constructor!==t.constructor)return!1;var i,r;if(Array.isArray(e)){if((r=e.length)!==t.length)return!1;for(i=r;0!=i--;)if(!s(e[i],t[i]))return!1;return!0}if(e instanceof Map&&t instanceof Map){if(e.size!==t.size)return!1;var o,n=(0,a.A)(e.entries());try{for(n.s();!(o=n.n()).done;)if(i=o.value,!t.has(i[0]))return!1}catch(p){n.e(p)}finally{n.f()}var l,c=(0,a.A)(e.entries());try{for(c.s();!(l=c.n()).done;)if(i=l.value,!s(i[1],t.get(i[0])))return!1}catch(p){c.e(p)}finally{c.f()}return!0}if(e instanceof Set&&t instanceof Set){if(e.size!==t.size)return!1;var h,d=(0,a.A)(e.entries());try{for(d.s();!(h=d.n()).done;)if(i=h.value,!t.has(i[0]))return!1}catch(p){d.e(p)}finally{d.f()}return!0}if(ArrayBuffer.isView(e)&&ArrayBuffer.isView(t)){if((r=e.length)!==t.length)return!1;for(i=r;0!=i--;)if(e[i]!==t[i])return!1;return!0}if(e.constructor===RegExp)return e.source===t.source&&e.flags===t.flags;if(e.valueOf!==Object.prototype.valueOf)return e.valueOf()===t.valueOf();if(e.toString!==Object.prototype.toString)return e.toString()===t.toString();var u=Object.keys(e);if((r=u.length)!==Object.keys(t).length)return!1;for(i=r;0!=i--;)if(!Object.prototype.hasOwnProperty.call(t,u[i]))return!1;for(i=r;0!=i--;){var v=u[i];if(!s(e[v],t[v]))return!1}return!0}return e!=e&&t!=t})},12924:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),s=i(56038),r=i(69683),o=i(6454),n=(i(28706),i(62062),i(18111),i(61701),i(26099),i(62826)),l=(i(44354),i(96196)),c=i(77845),h=i(92542),d=i(89473),u=(i(60961),e([d]));d=(u.then?(await u)():u)[0];var v,p,_,g,m=e=>e,f=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,s=new Array(i),o=0;o<i;o++)s[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(s))).size="medium",e.nowrap=!1,e.fullWidth=!1,e.variant="brand",e}return(0,o.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,l.qy)(v||(v=m`
      <wa-button-group childSelector="ha-button">
        ${0}
      </wa-button-group>
    `),this.buttons.map((e=>(0,l.qy)(p||(p=m`<ha-button
              iconTag="ha-svg-icon"
              class="icon"
              .variant=${0}
              .size=${0}
              .value=${0}
              @click=${0}
              .title=${0}
              .appearance=${0}
            >
              ${0}
            </ha-button>`),this.active===e.value&&this.activeVariant?this.activeVariant:this.variant,this.size,e.value,this._handleClick,e.label,this.active===e.value?"accent":"filled",e.iconPath?(0,l.qy)(_||(_=m`<ha-svg-icon
                    aria-label=${0}
                    .path=${0}
                  ></ha-svg-icon>`),e.label,e.iconPath):e.label))))}},{key:"_handleClick",value:function(e){this.active=e.currentTarget.value,(0,h.r)(this,"value-changed",{value:this.active})}}])}(l.WF);f.styles=(0,l.AH)(g||(g=m`
    :host {
      --mdc-icon-size: var(--button-toggle-icon-size, 20px);
    }

    :host([no-wrap]) wa-button-group::part(base) {
      flex-wrap: nowrap;
    }

    wa-button-group {
      padding: var(--ha-button-toggle-group-padding);
    }

    :host([full-width]) wa-button-group,
    :host([full-width]) wa-button-group::part(base) {
      width: 100%;
    }

    :host([full-width]) ha-button {
      flex: 1;
    }
  `)),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],f.prototype,"buttons",void 0),(0,n.__decorate)([(0,c.MZ)()],f.prototype,"active",void 0),(0,n.__decorate)([(0,c.MZ)({reflect:!0})],f.prototype,"size",void 0),(0,n.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0,attribute:"no-wrap"})],f.prototype,"nowrap",void 0),(0,n.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0,attribute:"full-width"})],f.prototype,"fullWidth",void 0),(0,n.__decorate)([(0,c.MZ)()],f.prototype,"variant",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:"active-variant"})],f.prototype,"activeVariant",void 0),f=(0,n.__decorate)([(0,c.EM)("ha-button-toggle-group")],f),t()}catch(y){t(y)}}))},55676:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{D:function(){return b}});var s=i(44734),r=i(56038),o=i(69683),n=i(6454),l=i(62826),c=i(96196),h=i(77845),d=i(45847),u=i(41144),v=i(43197),p=(i(22598),i(60961),e([v]));v=(p.then?(await p)():p)[0];var _,g,m,f,y=e=>e,b={device:"M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",and:"M4.4,16.5C4.4,15.6 4.7,14.7 5.2,13.9C5.7,13.1 6.7,12.2 8.2,11.2C7.3,10.1 6.8,9.3 6.5,8.7C6.1,8 6,7.4 6,6.7C6,5.2 6.4,4.1 7.3,3.2C8.2,2.3 9.4,2 10.9,2C12.2,2 13.3,2.4 14.2,3.2C15.1,4 15.5,5 15.5,6.1C15.5,6.9 15.3,7.6 14.9,8.3C14.5,9 13.8,9.7 12.8,10.4L11.4,11.5L15.7,16.7C16.3,15.5 16.6,14.3 16.6,12.8H18.8C18.8,15.1 18.3,17 17.2,18.5L20,21.8H17L15.7,20.3C15,20.9 14.3,21.3 13.4,21.6C12.5,21.9 11.6,22.1 10.7,22.1C8.8,22.1 7.3,21.6 6.1,20.6C5,19.5 4.4,18.2 4.4,16.5M10.7,20C12,20 13.2,19.5 14.3,18.5L9.6,12.8L9.2,13.1C7.7,14.2 7,15.3 7,16.5C7,17.6 7.3,18.4 8,19C8.7,19.6 9.5,20 10.7,20M8.5,6.7C8.5,7.6 9,8.6 10.1,9.9L11.7,8.8C12.3,8.4 12.7,8 12.9,7.6C13.1,7.2 13.2,6.7 13.2,6.2C13.2,5.6 13,5.1 12.5,4.7C12.1,4.3 11.5,4.1 10.8,4.1C10.1,4.1 9.5,4.3 9.1,4.8C8.7,5.3 8.5,5.9 8.5,6.7Z",or:"M2,4C5,10 5,14 2,20H8C13,20 19,16 22,12C19,8 13,4 8,4H2M5,6H8C11.5,6 16.3,9 19.3,12C16.3,15 11.5,18 8,18H5C6.4,13.9 6.4,10.1 5,6Z",not:"M14.08,4.61L15.92,5.4L14.8,8H19V10H13.95L12.23,14H19V16H11.38L9.92,19.4L8.08,18.61L9.2,16H5V14H10.06L11.77,10H5V8H12.63L14.08,4.61Z",state:"M6.27 17.05C6.72 17.58 7 18.25 7 19C7 20.66 5.66 22 4 22S1 20.66 1 19 2.34 16 4 16C4.18 16 4.36 16 4.53 16.05L7.6 10.69L5.86 9.7L9.95 8.58L11.07 12.67L9.33 11.68L6.27 17.05M20 16C18.7 16 17.6 16.84 17.18 18H11V16L8 19L11 22V20H17.18C17.6 21.16 18.7 22 20 22C21.66 22 23 20.66 23 19S21.66 16 20 16M12 8C12.18 8 12.36 8 12.53 7.95L15.6 13.31L13.86 14.3L17.95 15.42L19.07 11.33L17.33 12.32L14.27 6.95C14.72 6.42 15 5.75 15 5C15 3.34 13.66 2 12 2S9 3.34 9 5 10.34 8 12 8Z",numeric_state:"M4,17V9H2V7H6V17H4M22,15C22,16.11 21.1,17 20,17H16V15H20V13H18V11H20V9H16V7H20A2,2 0 0,1 22,9V10.5A1.5,1.5 0 0,1 20.5,12A1.5,1.5 0 0,1 22,13.5V15M14,15V17H8V13C8,11.89 8.9,11 10,11H12V9H8V7H12A2,2 0 0,1 14,9V11C14,12.11 13.1,13 12,13H10V15H14Z",sun:"M12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,2L14.39,5.42C13.65,5.15 12.84,5 12,5C11.16,5 10.35,5.15 9.61,5.42L12,2M3.34,7L7.5,6.65C6.9,7.16 6.36,7.78 5.94,8.5C5.5,9.24 5.25,10 5.11,10.79L3.34,7M3.36,17L5.12,13.23C5.26,14 5.53,14.78 5.95,15.5C6.37,16.24 6.91,16.86 7.5,17.37L3.36,17M20.65,7L18.88,10.79C18.74,10 18.47,9.23 18.05,8.5C17.63,7.78 17.1,7.15 16.5,6.64L20.65,7M20.64,17L16.5,17.36C17.09,16.85 17.62,16.22 18.04,15.5C18.46,14.77 18.73,14 18.87,13.21L20.64,17M12,22L9.59,18.56C10.33,18.83 11.14,19 12,19C12.82,19 13.63,18.83 14.37,18.56L12,22Z",template:"M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z",time:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z",trigger:"M10 7V9H9V15H10V17H6V15H7V9H6V7H10M16 7C17.11 7 18 7.9 18 9V15C18 16.11 17.11 17 16 17H12V7M16 9H14V15H16V9Z",zone:"M12,2C15.31,2 18,4.66 18,7.95C18,12.41 12,19 12,19C12,19 6,12.41 6,7.95C6,4.66 8.69,2 12,2M12,6A2,2 0 0,0 10,8A2,2 0 0,0 12,10A2,2 0 0,0 14,8A2,2 0 0,0 12,6M20,19C20,21.21 16.42,23 12,23C7.58,23 4,21.21 4,19C4,17.71 5.22,16.56 7.11,15.83L7.75,16.74C6.67,17.19 6,17.81 6,18.5C6,19.88 8.69,21 12,21C15.31,21 18,19.88 18,18.5C18,17.81 17.33,17.19 16.25,16.74L16.89,15.83C18.78,16.56 20,17.71 20,19Z"},$=function(e){function t(){return(0,s.A)(this,t),(0,o.A)(this,t,arguments)}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){if(this.icon)return(0,c.qy)(_||(_=y`<ha-icon .icon=${0}></ha-icon>`),this.icon);if(!this.condition)return c.s6;if(!this.hass)return this._renderFallback();var e=(0,v.r)(this.hass,this.condition).then((e=>e?(0,c.qy)(g||(g=y`<ha-icon .icon=${0}></ha-icon>`),e):this._renderFallback()));return(0,c.qy)(m||(m=y`${0}`),(0,d.T)(e))}},{key:"_renderFallback",value:function(){var e=(0,u.m)(this.condition);return(0,c.qy)(f||(f=y`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),b[this.condition]||v.l[e])}}])}(c.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)()],$.prototype,"condition",void 0),(0,l.__decorate)([(0,h.MZ)()],$.prototype,"icon",void 0),$=(0,l.__decorate)([(0,h.EM)("ha-condition-icon")],$),a()}catch(A){a(A)}}))},85695:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),s=i(56038),r=i(69683),o=i(6454),n=i(62826),l=i(96196),c=i(77845),h=i(45847),d=i(43197),u=i(76681),v=(i(22598),e([d]));d=(v.then?(await v)():v)[0];var p,_,g,m,f,y,b,$=e=>e,A=function(e){function t(){return(0,a.A)(this,t),(0,r.A)(this,t,arguments)}return(0,o.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){if(this.icon)return(0,l.qy)(p||(p=$`<ha-icon .icon=${0}></ha-icon>`),this.icon);if(!this.domain)return l.s6;if(!this.hass)return this._renderFallback();var e=(0,d._4)(this.hass,this.domain,this.deviceClass,this.state).then((e=>e?(0,l.qy)(_||(_=$`<ha-icon .icon=${0}></ha-icon>`),e):this._renderFallback()));return(0,l.qy)(g||(g=$`${0}`),(0,h.T)(e))}},{key:"_renderFallback",value:function(){if(this.domain&&this.domain in d.l)return(0,l.qy)(m||(m=$`
        <ha-svg-icon .path=${0}></ha-svg-icon>
      `),d.l[this.domain]);if(this.brandFallback){var e,t=(0,u.MR)({domain:this.domain,type:"icon",darkOptimized:null===(e=this.hass.themes)||void 0===e?void 0:e.darkMode});return(0,l.qy)(f||(f=$`
        <img
          alt=""
          src=${0}
          crossorigin="anonymous"
          referrerpolicy="no-referrer"
        />
      `),t)}return(0,l.qy)(y||(y=$`<ha-svg-icon .path=${0}></ha-svg-icon>`),d.lW)}}])}(l.WF);A.styles=(0,l.AH)(b||(b=$`
    img {
      width: var(--mdc-icon-size, 24px);
    }
  `)),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,n.__decorate)([(0,c.MZ)()],A.prototype,"domain",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"deviceClass",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"state",void 0),(0,n.__decorate)([(0,c.MZ)()],A.prototype,"icon",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:"brand-fallback",type:Boolean})],A.prototype,"brandFallback",void 0),A=(0,n.__decorate)([(0,c.EM)("ha-domain-icon")],A),t()}catch(C){t(C)}}))},80263:function(e,t,i){i.r(t),i.d(t,{HaIconButtonPrev:function(){return v}});var a,s=i(44734),r=i(56038),o=i(69683),n=i(6454),l=(i(28706),i(62826)),c=i(96196),h=i(77845),d=i(76679),u=(i(60733),e=>e),v=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,o.A)(this,t,[].concat(a))).disabled=!1,e._icon="rtl"===d.G.document.dir?"M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z":"M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e;return(0,c.qy)(a||(a=u`
      <ha-icon-button
        .disabled=${0}
        .label=${0}
        .path=${0}
      ></ha-icon-button>
    `),this.disabled,this.label||(null===(e=this.hass)||void 0===e?void 0:e.localize("ui.common.back"))||"Back",this._icon)}}])}(c.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],v.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.MZ)()],v.prototype,"label",void 0),(0,l.__decorate)([(0,h.wk)()],v.prototype,"_icon",void 0),v=(0,l.__decorate)([(0,h.EM)("ha-icon-button-prev")],v)},63426:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),s=i(56038),r=i(69683),o=i(6454),n=i(62826),l=i(96196),c=i(77845),h=i(45847),d=i(41144),u=i(43197),v=(i(22598),i(60961),e([u]));u=(v.then?(await v)():v)[0];var p,_,g,m,f=e=>e,y=function(e){function t(){return(0,a.A)(this,t),(0,r.A)(this,t,arguments)}return(0,o.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){if(this.icon)return(0,l.qy)(p||(p=f`<ha-icon .icon=${0}></ha-icon>`),this.icon);if(!this.service)return l.s6;if(!this.hass)return this._renderFallback();var e=(0,u.f$)(this.hass,this.service).then((e=>e?(0,l.qy)(_||(_=f`<ha-icon .icon=${0}></ha-icon>`),e):this._renderFallback()));return(0,l.qy)(g||(g=f`${0}`),(0,h.T)(e))}},{key:"_renderFallback",value:function(){var e=(0,d.m)(this.service);return(0,l.qy)(m||(m=f`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),u.l[e]||u.Gn)}}])}(l.WF);(0,n.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,n.__decorate)([(0,c.MZ)()],y.prototype,"service",void 0),(0,n.__decorate)([(0,c.MZ)()],y.prototype,"icon",void 0),y=(0,n.__decorate)([(0,c.EM)("ha-service-icon")],y),t()}catch(b){t(b)}}))},58103:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{S:function(){return $}});var s=i(44734),r=i(56038),o=i(69683),n=i(6454),l=i(62826),c=i(96196),h=i(77845),d=i(45847),u=i(41144),v=i(43197),p=i(7053),_=(i(22598),i(60961),e([v]));v=(_.then?(await _)():_)[0];var g,m,f,y,b=e=>e,$={calendar:"M19,19H5V8H19M16,1V3H8V1H6V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3H18V1M17,12H12V17H17V12Z",device:"M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",event:"M10,9A1,1 0 0,1 11,8A1,1 0 0,1 12,9V13.47L13.21,13.6L18.15,15.79C18.68,16.03 19,16.56 19,17.14V21.5C18.97,22.32 18.32,22.97 17.5,23H11C10.62,23 10.26,22.85 10,22.57L5.1,18.37L5.84,17.6C6.03,17.39 6.3,17.28 6.58,17.28H6.8L10,19V9M11,5A4,4 0 0,1 15,9C15,10.5 14.2,11.77 13,12.46V11.24C13.61,10.69 14,9.89 14,9A3,3 0 0,0 11,6A3,3 0 0,0 8,9C8,9.89 8.39,10.69 9,11.24V12.46C7.8,11.77 7,10.5 7,9A4,4 0 0,1 11,5M11,3A6,6 0 0,1 17,9C17,10.7 16.29,12.23 15.16,13.33L14.16,12.88C15.28,11.96 16,10.56 16,9A5,5 0 0,0 11,4A5,5 0 0,0 6,9C6,11.05 7.23,12.81 9,13.58V14.66C6.67,13.83 5,11.61 5,9A6,6 0 0,1 11,3Z",state:"M6.27 17.05C6.72 17.58 7 18.25 7 19C7 20.66 5.66 22 4 22S1 20.66 1 19 2.34 16 4 16C4.18 16 4.36 16 4.53 16.05L7.6 10.69L5.86 9.7L9.95 8.58L11.07 12.67L9.33 11.68L6.27 17.05M20 16C18.7 16 17.6 16.84 17.18 18H11V16L8 19L11 22V20H17.18C17.6 21.16 18.7 22 20 22C21.66 22 23 20.66 23 19S21.66 16 20 16M12 8C12.18 8 12.36 8 12.53 7.95L15.6 13.31L13.86 14.3L17.95 15.42L19.07 11.33L17.33 12.32L14.27 6.95C14.72 6.42 15 5.75 15 5C15 3.34 13.66 2 12 2S9 3.34 9 5 10.34 8 12 8Z",geo_location:"M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z",homeassistant:p.mdiHomeAssistant,mqtt:"M21,9L17,5V8H10V10H17V13M7,11L3,15L7,19V16H14V14H7V11Z",numeric_state:"M4,17V9H2V7H6V17H4M22,15C22,16.11 21.1,17 20,17H16V15H20V13H18V11H20V9H16V7H20A2,2 0 0,1 22,9V10.5A1.5,1.5 0 0,1 20.5,12A1.5,1.5 0 0,1 22,13.5V15M14,15V17H8V13C8,11.89 8.9,11 10,11H12V9H8V7H12A2,2 0 0,1 14,9V11C14,12.11 13.1,13 12,13H10V15H14Z",sun:"M12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,2L14.39,5.42C13.65,5.15 12.84,5 12,5C11.16,5 10.35,5.15 9.61,5.42L12,2M3.34,7L7.5,6.65C6.9,7.16 6.36,7.78 5.94,8.5C5.5,9.24 5.25,10 5.11,10.79L3.34,7M3.36,17L5.12,13.23C5.26,14 5.53,14.78 5.95,15.5C6.37,16.24 6.91,16.86 7.5,17.37L3.36,17M20.65,7L18.88,10.79C18.74,10 18.47,9.23 18.05,8.5C17.63,7.78 17.1,7.15 16.5,6.64L20.65,7M20.64,17L16.5,17.36C17.09,16.85 17.62,16.22 18.04,15.5C18.46,14.77 18.73,14 18.87,13.21L20.64,17M12,22L9.59,18.56C10.33,18.83 11.14,19 12,19C12.82,19 13.63,18.83 14.37,18.56L12,22Z",conversation:"M8,7A2,2 0 0,1 10,9V14A2,2 0 0,1 8,16A2,2 0 0,1 6,14V9A2,2 0 0,1 8,7M14,14C14,16.97 11.84,19.44 9,19.92V22H7V19.92C4.16,19.44 2,16.97 2,14H4A4,4 0 0,0 8,18A4,4 0 0,0 12,14H14M21.41,9.41L17.17,13.66L18.18,10H14A2,2 0 0,1 12,8V4A2,2 0 0,1 14,2H20A2,2 0 0,1 22,4V8C22,8.55 21.78,9.05 21.41,9.41Z",tag:"M18,6H13A2,2 0 0,0 11,8V10.28C10.41,10.62 10,11.26 10,12A2,2 0 0,0 12,14C13.11,14 14,13.1 14,12C14,11.26 13.6,10.62 13,10.28V8H16V16H8V8H10V6H8L6,6V18H18M20,20H4V4H20M20,2H4A2,2 0 0,0 2,4V20A2,2 0 0,0 4,22H20C21.11,22 22,21.1 22,20V4C22,2.89 21.11,2 20,2Z",template:"M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z",time:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z",time_pattern:"M11,17A1,1 0 0,0 12,18A1,1 0 0,0 13,17A1,1 0 0,0 12,16A1,1 0 0,0 11,17M11,3V7H13V5.08C16.39,5.57 19,8.47 19,12A7,7 0 0,1 12,19A7,7 0 0,1 5,12C5,10.32 5.59,8.78 6.58,7.58L12,13L13.41,11.59L6.61,4.79V4.81C4.42,6.45 3,9.05 3,12A9,9 0 0,0 12,21A9,9 0 0,0 21,12A9,9 0 0,0 12,3M18,12A1,1 0 0,0 17,11A1,1 0 0,0 16,12A1,1 0 0,0 17,13A1,1 0 0,0 18,12M6,12A1,1 0 0,0 7,13A1,1 0 0,0 8,12A1,1 0 0,0 7,11A1,1 0 0,0 6,12Z",webhook:"M10.46,19C9,21.07 6.15,21.59 4.09,20.15C2.04,18.71 1.56,15.84 3,13.75C3.87,12.5 5.21,11.83 6.58,11.77L6.63,13.2C5.72,13.27 4.84,13.74 4.27,14.56C3.27,16 3.58,17.94 4.95,18.91C6.33,19.87 8.26,19.5 9.26,18.07C9.57,17.62 9.75,17.13 9.82,16.63V15.62L15.4,15.58L15.47,15.47C16,14.55 17.15,14.23 18.05,14.75C18.95,15.27 19.26,16.43 18.73,17.35C18.2,18.26 17.04,18.58 16.14,18.06C15.73,17.83 15.44,17.46 15.31,17.04L11.24,17.06C11.13,17.73 10.87,18.38 10.46,19M17.74,11.86C20.27,12.17 22.07,14.44 21.76,16.93C21.45,19.43 19.15,21.2 16.62,20.89C15.13,20.71 13.9,19.86 13.19,18.68L14.43,17.96C14.92,18.73 15.75,19.28 16.75,19.41C18.5,19.62 20.05,18.43 20.26,16.76C20.47,15.09 19.23,13.56 17.5,13.35C16.96,13.29 16.44,13.36 15.97,13.53L15.12,13.97L12.54,9.2H12.32C11.26,9.16 10.44,8.29 10.47,7.25C10.5,6.21 11.4,5.4 12.45,5.44C13.5,5.5 14.33,6.35 14.3,7.39C14.28,7.83 14.11,8.23 13.84,8.54L15.74,12.05C16.36,11.85 17.04,11.78 17.74,11.86M8.25,9.14C7.25,6.79 8.31,4.1 10.62,3.12C12.94,2.14 15.62,3.25 16.62,5.6C17.21,6.97 17.09,8.47 16.42,9.67L15.18,8.95C15.6,8.14 15.67,7.15 15.27,6.22C14.59,4.62 12.78,3.85 11.23,4.5C9.67,5.16 8.97,7 9.65,8.6C9.93,9.26 10.4,9.77 10.97,10.11L11.36,10.32L8.29,15.31C8.32,15.36 8.36,15.42 8.39,15.5C8.88,16.41 8.54,17.56 7.62,18.05C6.71,18.54 5.56,18.18 5.06,17.24C4.57,16.31 4.91,15.16 5.83,14.67C6.22,14.46 6.65,14.41 7.06,14.5L9.37,10.73C8.9,10.3 8.5,9.76 8.25,9.14Z",persistent_notification:"M13 11H11V5H13M13 15H11V13H13M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z",zone:"M12,2C15.31,2 18,4.66 18,7.95C18,12.41 12,19 12,19C12,19 6,12.41 6,7.95C6,4.66 8.69,2 12,2M12,6A2,2 0 0,0 10,8A2,2 0 0,0 12,10A2,2 0 0,0 14,8A2,2 0 0,0 12,6M20,19C20,21.21 16.42,23 12,23C7.58,23 4,21.21 4,19C4,17.71 5.22,16.56 7.11,15.83L7.75,16.74C6.67,17.19 6,17.81 6,18.5C6,19.88 8.69,21 12,21C15.31,21 18,19.88 18,18.5C18,17.81 17.33,17.19 16.25,16.74L16.89,15.83C18.78,16.56 20,17.71 20,19Z",list:"M7,5H21V7H7V5M7,13V11H21V13H7M4,4.5A1.5,1.5 0 0,1 5.5,6A1.5,1.5 0 0,1 4,7.5A1.5,1.5 0 0,1 2.5,6A1.5,1.5 0 0,1 4,4.5M4,10.5A1.5,1.5 0 0,1 5.5,12A1.5,1.5 0 0,1 4,13.5A1.5,1.5 0 0,1 2.5,12A1.5,1.5 0 0,1 4,10.5M7,19V17H21V19H7M4,16.5A1.5,1.5 0 0,1 5.5,18A1.5,1.5 0 0,1 4,19.5A1.5,1.5 0 0,1 2.5,18A1.5,1.5 0 0,1 4,16.5Z"},A=function(e){function t(){return(0,s.A)(this,t),(0,o.A)(this,t,arguments)}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){if(this.icon)return(0,c.qy)(g||(g=b`<ha-icon .icon=${0}></ha-icon>`),this.icon);if(!this.trigger)return c.s6;if(!this.hass)return this._renderFallback();var e=(0,v.ab)(this.hass,this.trigger).then((e=>e?(0,c.qy)(m||(m=b`<ha-icon .icon=${0}></ha-icon>`),e):this._renderFallback()));return(0,c.qy)(f||(f=b`${0}`),(0,d.T)(e))}},{key:"_renderFallback",value:function(){var e=(0,u.m)(this.trigger);return(0,c.qy)(y||(y=b`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),$[this.trigger]||v.l[e])}}])}(c.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)()],A.prototype,"trigger",void 0),(0,l.__decorate)([(0,h.MZ)()],A.prototype,"icon",void 0),A=(0,l.__decorate)([(0,h.EM)("ha-trigger-icon")],A),a()}catch(C){a(C)}}))},265:function(e,t,i){i.d(t,{EN:function(){return l},I8:function(){return d},L_:function(){return h},MC:function(){return c},O$:function(){return s},bM:function(){return n},ix:function(){return r},rP:function(){return o}});i(23792),i(26099),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(62953);var a="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z",s={condition:"M4 2A2 2 0 0 0 2 4V12H4V8H6V12H8V4A2 2 0 0 0 6 2H4M4 4H6V6H4M22 15.5V14A2 2 0 0 0 20 12H16V22H20A2 2 0 0 0 22 20V18.5A1.54 1.54 0 0 0 20.5 17A1.54 1.54 0 0 0 22 15.5M20 20H18V18H20V20M20 16H18V14H20M5.79 21.61L4.21 20.39L18.21 2.39L19.79 3.61Z",delay:"M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z",event:"M10,9A1,1 0 0,1 11,8A1,1 0 0,1 12,9V13.47L13.21,13.6L18.15,15.79C18.68,16.03 19,16.56 19,17.14V21.5C18.97,22.32 18.32,22.97 17.5,23H11C10.62,23 10.26,22.85 10,22.57L5.1,18.37L5.84,17.6C6.03,17.39 6.3,17.28 6.58,17.28H6.8L10,19V9M11,5A4,4 0 0,1 15,9C15,10.5 14.2,11.77 13,12.46V11.24C13.61,10.69 14,9.89 14,9A3,3 0 0,0 11,6A3,3 0 0,0 8,9C8,9.89 8.39,10.69 9,11.24V12.46C7.8,11.77 7,10.5 7,9A4,4 0 0,1 11,5M11,3A6,6 0 0,1 17,9C17,10.7 16.29,12.23 15.16,13.33L14.16,12.88C15.28,11.96 16,10.56 16,9A5,5 0 0,0 11,4A5,5 0 0,0 6,9C6,11.05 7.23,12.81 9,13.58V14.66C6.67,13.83 5,11.61 5,9A6,6 0 0,1 11,3Z",play_media:"M8,5.14V19.14L19,12.14L8,5.14Z",service:"M12,5A2,2 0 0,1 14,7C14,7.24 13.96,7.47 13.88,7.69C17.95,8.5 21,11.91 21,16H3C3,11.91 6.05,8.5 10.12,7.69C10.04,7.47 10,7.24 10,7A2,2 0 0,1 12,5M22,19H2V17H22V19Z",wait_template:"M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z",wait_for_trigger:"M12,9A2,2 0 0,1 10,7C10,5.89 10.9,5 12,5C13.11,5 14,5.89 14,7A2,2 0 0,1 12,9M12,14A2,2 0 0,1 10,12C10,10.89 10.9,10 12,10C13.11,10 14,10.89 14,12A2,2 0 0,1 12,14M12,19A2,2 0 0,1 10,17C10,15.89 10.9,15 12,15C13.11,15 14,15.89 14,17A2,2 0 0,1 12,19M20,10H17V8.86C18.72,8.41 20,6.86 20,5H17V4A1,1 0 0,0 16,3H8A1,1 0 0,0 7,4V5H4C4,6.86 5.28,8.41 7,8.86V10H4C4,11.86 5.28,13.41 7,13.86V15H4C4,16.86 5.28,18.41 7,18.86V20A1,1 0 0,0 8,21H16A1,1 0 0,0 17,20V18.86C18.72,18.41 20,16.86 20,15H17V13.86C18.72,13.41 20,11.86 20,10Z",repeat:a,repeat_count:a,repeat_while:a,repeat_until:a,repeat_for_each:a,choose:"M11,5H8L12,1L16,5H13V9.43C12.25,9.89 11.58,10.46 11,11.12V5M22,11L18,7V10C14.39,9.85 11.31,12.57 11,16.17C9.44,16.72 8.62,18.44 9.17,20C9.72,21.56 11.44,22.38 13,21.83C14.56,21.27 15.38,19.56 14.83,18C14.53,17.14 13.85,16.47 13,16.17C13.47,12.17 17.47,11.97 17.95,11.97V14.97L22,11M10.63,11.59C9.3,10.57 7.67,10 6,10V7L2,11L6,15V12C7.34,12.03 8.63,12.5 9.64,13.4C9.89,12.76 10.22,12.15 10.63,11.59Z",if:"M14,4L16.29,6.29L13.41,9.17L14.83,10.59L17.71,7.71L20,10V4M10,4H4V10L6.29,7.71L11,12.41V20H13V11.59L7.71,6.29",device_id:"M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",stop:"M13 24C9.74 24 6.81 22 5.6 19L2.57 11.37C2.26 10.58 3 9.79 3.81 10.05L4.6 10.31C5.16 10.5 5.62 10.92 5.84 11.47L7.25 15H8V3.25C8 2.56 8.56 2 9.25 2S10.5 2.56 10.5 3.25V12H11.5V1.25C11.5 .56 12.06 0 12.75 0S14 .56 14 1.25V12H15V2.75C15 2.06 15.56 1.5 16.25 1.5C16.94 1.5 17.5 2.06 17.5 2.75V12H18.5V5.75C18.5 5.06 19.06 4.5 19.75 4.5S21 5.06 21 5.75V16C21 20.42 17.42 24 13 24Z",sequence:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",parallel:"M16,4.5V7H5V9H16V11.5L19.5,8M16,12.5V15H5V17H16V19.5L19.5,16",variables:"M21 2H3C1.9 2 1 2.9 1 4V20C1 21.1 1.9 22 3 22H21C22.1 22 23 21.1 23 20V4C23 2.9 22.1 2 21 2M21 20H3V6H21V20M16.6 8C18.1 9.3 19 11.1 19 13C19 14.9 18.1 16.7 16.6 18L15 17.4C16.3 16.4 17 14.7 17 13S16.3 9.6 15 8.6L16.6 8M7.4 8L9 8.6C7.7 9.6 7 11.3 7 13S7.7 16.4 9 17.4L7.4 18C5.9 16.7 5 14.9 5 13S5.9 9.3 7.4 8M12.1 12L13.5 10H15L12.8 13L14.1 16H12.8L12 14L10.6 16H9L11.3 12.9L10 10H11.3L12.1 12Z",set_conversation_response:"M12,8H4A2,2 0 0,0 2,10V14A2,2 0 0,0 4,16H5V20A1,1 0 0,0 6,21H8A1,1 0 0,0 9,20V16H12L17,20V4L12,8M21.5,12C21.5,13.71 20.54,15.26 19,16V8C20.53,8.75 21.5,10.3 21.5,12Z"},r=new Set(["variables"]),o=[{groups:{device_id:{},dynamicGroups:{}}},{titleKey:"ui.panel.config.automation.editor.actions.groups.helpers.label",groups:{helpers:{}}},{titleKey:"ui.panel.config.automation.editor.actions.groups.other.label",groups:{event:{},service:{},set_conversation_response:{},other:{}}}],n={condition:{},delay:{},wait_template:{},wait_for_trigger:{},repeat_count:{},repeat_while:{},repeat_until:{},repeat_for_each:{},choose:{},if:{},stop:{},sequence:{},parallel:{},variables:{}},l={repeat_count:{repeat:{count:2,sequence:[]}},repeat_while:{repeat:{while:[],sequence:[]}},repeat_until:{repeat:{until:[],sequence:[]}},repeat_for_each:{repeat:{for_each:{},sequence:[]}}},c=["ha-automation-action-choose","ha-automation-action-condition","ha-automation-action-if","ha-automation-action-parallel","ha-automation-action-repeat","ha-automation-action-sequence"],h=["choose","if","parallel","sequence","repeat_while","repeat_until"],d=["repeat_count","repeat_for_each","wait_for_trigger"]},53083:function(e,t,i){i.d(t,{KD:function(){return s},_o:function(){return r}});var a=i(31432),s=(i(44114),(e,t)=>e.callWS(Object.assign({type:"config/floor_registry/create"},t))),r=e=>{var t,i={},s=(0,a.A)(e);try{for(s.s();!(t=s.n()).done;){var r=t.value;r.floor_id&&(r.floor_id in i||(i[r.floor_id]=[]),i[r.floor_id].push(r))}}catch(o){s.e(o)}finally{s.f()}return i}},14332:function(e,t,i){i.d(t,{b:function(){return l}});var a=i(44734),s=i(56038),r=i(69683),o=i(6454),n=i(25460),l=(i(28706),i(26099),i(38781),i(18111),i(13579),e=>{var t=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,s=new Array(i),o=0;o<i;o++)s[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(s)))._keydownEvent=t=>{var i=e.supportedShortcuts(),a=t.shiftKey?t.key.toUpperCase():t.key;if((t.ctrlKey||t.metaKey)&&!t.altKey&&a in i){var s;if(!(e=>{var t;if(e.some((e=>"tagName"in e&&("HA-MENU"===e.tagName||"HA-CODE-EDITOR"===e.tagName))))return!1;var i=e[0];if("TEXTAREA"===i.tagName)return!1;if("HA-SELECT"===(null===(t=i.parentElement)||void 0===t?void 0:t.tagName))return!1;if("INPUT"!==i.tagName)return!0;switch(i.type){case"button":case"checkbox":case"hidden":case"radio":case"range":return!0;default:return!1}})(t.composedPath()))return;if(null!==(s=window.getSelection())&&void 0!==s&&s.toString())return;return t.preventDefault(),void i[a]()}var r=e.supportedSingleKeyShortcuts();a in r&&(t.preventDefault(),r[a]())},e._listenersAdded=!1,e}return(0,o.A)(t,e),(0,s.A)(t,[{key:"connectedCallback",value:function(){(0,n.A)(t,"connectedCallback",this,3)([]),this.addKeyboardShortcuts()}},{key:"disconnectedCallback",value:function(){this.removeKeyboardShortcuts(),(0,n.A)(t,"disconnectedCallback",this,3)([])}},{key:"addKeyboardShortcuts",value:function(){this._listenersAdded||(this._listenersAdded=!0,window.addEventListener("keydown",this._keydownEvent))}},{key:"removeKeyboardShortcuts",value:function(){this._listenersAdded=!1,window.removeEventListener("keydown",this._keydownEvent)}},{key:"supportedShortcuts",value:function(){return{}}},{key:"supportedSingleKeyShortcuts",value:function(){return{}}}])}(e);return t})},53468:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t);var s=i(31432),r=i(61397),o=i(50264),n=i(94741),l=i(78261),c=i(44734),h=i(56038),d=i(75864),u=i(69683),v=i(6454),p=i(25460),_=(i(52675),i(89463),i(28706),i(2008),i(50113),i(46449),i(74423),i(25276),i(23792),i(62062),i(44114),i(72712),i(26910),i(93514),i(13609),i(18111),i(22489),i(20116),i(7588),i(61701),i(18237),i(13579),i(5506),i(53921),i(26099),i(16034),i(27495),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(25440),i(90744),i(46058),i(23500),i(62953),i(62826)),g=i(16527),m=i(96196),f=i(77845),y=i(94333),b=i(4937),$=i(22786),A=i(92542),C=i(76679),k=i(56403),V=i(16727),H=i(41144),w=i(79384),L=i(47644),M=i(25749),x=i(79599),S=i(40404),I=i(38852),O=i(91720),j=i(92312),z=i(89473),G=i(12924),T=(i(94343),i(55676)),q=(i(86451),i(85695)),E=(i(26537),i(22598),i(60733),i(80263),i(28608),i(32072),i(42921),i(23897),i(12109),i(63426)),D=i(88422),Z=i(58103),F=i(36626),B=(i(17262),i(265)),P=i(54110),W=i(80812),K=i(10038),N=i(3950),U=i(34972),R=i(1491),J=i(53083),Q=i(43197),X=i(84125),Y=i(78991),ee=i(6098),te=i(98995),ie=i(14332),ae=i(98315),se=i(4848),re=i(90840),oe=i(48086),ne=i(28864),le=i(78232),ce=e([O,j,z,G,q,E,D,F,re,oe,ne,Z,T,Q]);[O,j,z,G,q,E,D,F,re,oe,ne,Z,T,Q]=ce.then?(await ce)():ce;var he,de,ue,ve,pe,_e,ge,me,fe,ye,be,$e,Ae,Ce,ke,Ve,He,we,Le,Me,xe,Se,Ie,Oe,je,ze,Ge,Te,qe,Ee,De,Ze=e=>e,Fe={trigger:{collections:te.NI,icons:Z.S},condition:{collections:K.GS,icons:T.D},action:{collections:B.rP,icons:B.O$}},Be=new Set(["date","datetime","device_tracker","text","time","tts","update","weather","image_processing"]),Pe=new Set(["notify"]),We=["dynamicGroups","helpers","other"],Ke=function(e){function t(){var e;(0,c.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,u.A)(this,t,[].concat(a)))._open=!0,e._tab="targets",e._filter="",e._bottomSheetMode=!1,e._narrow=!1,e._triggerDescriptions={},e._loadItemsError=!1,e._newTriggersAndConditions=!1,e._conditionDescriptions={},e._configEntryLookup={},e._updateNarrow=()=>{e._narrow=window.matchMedia("(max-width: 870px)").matches||window.matchMedia("(max-height: 500px)").matches},e._getItems=()=>{var t;return e._filter||"blocks"!==e._tab?!e._filter&&"groups"===e._tab&&e._selectedGroup?[{title:e.hass.localize(`ui.panel.config.automation.editor.${e._params.type}s.name`),items:e._getGroupItems(e._params.type,e._selectedGroup,null!==(t=e._selectedCollectionIndex)&&void 0!==t?t:0,e._domains,e.hass.localize,e.hass.services,e._manifests)}]:!e._filter&&"targets"===e._tab&&e._selectedTarget&&e._targetItems?e._targetItems:void 0:[{title:e.hass.localize("ui.panel.config.automation.editor.blocks"),items:e._getBlockItems(e._params.type,e.hass.localize)}]},e._getGroups=(e,t,i)=>t&&void 0!==i?Fe[e].collections[i].groups[t].members||{[t]:{}}:Fe[e].collections.reduce(((e,t)=>Object.assign(Object.assign({},e),t.groups)),{}),e._items=(0,$.A)(((t,i,a,s)=>{var r=e._getGroups(t),o=a=>Object.entries(a).map((a=>{var s=(0,l.A)(a,2),r=s[0],n=s[1];return n.members?o(n.members):e._convertToItem(r,n,t,i)})),c=o(r).flat();return"trigger"===t?c.push.apply(c,(0,n.A)(e._triggers(i,e._triggerDescriptions))):"condition"===t?c.push.apply(c,(0,n.A)(e._conditions(i,e._conditionDescriptions,s))):"action"===t&&c.push.apply(c,(0,n.A)(e._services(i,a,s))),c.filter((e=>e.name))})),e._getCollections=(0,$.A)(((t,i,a,s,r,o,c,h)=>{var d=[];return i.forEach((i=>{var u=Object.entries(i.groups),v=[];"trigger"===t&&Object.keys(i.groups).some((e=>We.includes(e)))?(v.push.apply(v,(0,n.A)(e._triggerGroups(s,o,h,a,i.groups.dynamicGroups?void 0:i.groups.helpers?"helper":"other"))),u=u.filter((e=>{var t=(0,l.A)(e,1)[0];return!We.includes(t)}))):"condition"===t&&Object.keys(i.groups).some((e=>We.includes(e)))?(v.push.apply(v,(0,n.A)(e._conditionGroups(s,c,h,a,i.groups.dynamicGroups?void 0:i.groups.helpers?"helper":"other"))),u=u.filter((e=>{var t=(0,l.A)(e,1)[0];return!We.includes(t)}))):"action"===t&&Object.keys(i.groups).some((e=>We.includes(e)))&&(v.push.apply(v,(0,n.A)(e._serviceGroups(s,r,h,a,i.groups.dynamicGroups?void 0:i.groups.helpers?"helper":"other"))),u=u.filter((e=>{var t=(0,l.A)(e,1)[0];return!We.includes(t)}))),v.push.apply(v,(0,n.A)(u.map((i=>{var a=(0,l.A)(i,2),r=a[0],o=a[1];return e._convertToItem(r,o,t,s)})))),d.push({titleKey:i.titleKey,groups:v.sort(((t,i)=>"device"===t.key||"device_id"===t.key?-1:"device"===i.key||"device_id"===i.key?1:(0,M.xL)(t.name,i.name,e.hass.locale.language)))})})),d})),e._getBlockItems=(0,$.A)(((t,i)=>{var a="action"===t?B.bM:K.oW;return Object.entries(a).map((a=>{var s=(0,l.A)(a,2),r=s[0],o=s[1];return e._convertToItem(r,o,t,i)})).sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))})),e._getGroupItems=(0,$.A)(((t,i,a,s,r,o,c)=>{if("trigger"===t&&(0,W.Q)(i))return e._triggers(r,e._triggerDescriptions,i);if("condition"===t&&(0,W.Q)(i))return e._conditions(r,e._conditionDescriptions,c,i);if("action"===t&&(0,W.Q)(i))return e._services(r,o,c,i);var h=e._getGroups(t,i,a),d=Object.entries(h).map((i=>{var a=(0,l.A)(i,2),s=a[0],o=a[1];return e._convertToItem(s,o,t,r)}));return"action"===t&&(e._selectedGroup?"helpers"===e._selectedGroup?d.unshift.apply(d,(0,n.A)(e._serviceGroups(r,o,c,s,"helper"))):"other"===e._selectedGroup&&d.unshift.apply(d,(0,n.A)(e._serviceGroups(r,o,c,s,"other"))):d.unshift.apply(d,(0,n.A)(e._serviceGroups(r,o,c,s,void 0)))),d.sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))})),e._serviceGroups=(t,i,a,s,r)=>{if(!i||!a)return[];var o=[];return Object.keys(i).forEach((i=>{var n=a[i],l=!s||s.has(i);(void 0===r&&(Pe.has(i)||"entity"===(null==n?void 0:n.integration_type)&&l&&!Be.has(i))||"helper"===r&&"helper"===(null==n?void 0:n.integration_type)||"other"===r&&!Pe.has(i)&&(Be.has(i)||!l&&"entity"===(null==n?void 0:n.integration_type)||!["helper","entity"].includes((null==n?void 0:n.integration_type)||"")))&&o.push({icon:(0,m.qy)(he||(he=Ze`
            <ha-domain-icon
              .hass=${0}
              .domain=${0}
              brand-fallback
            ></ha-domain-icon>
          `),e.hass,i),key:`${W.VH}${i}`,name:(0,X.p$)(t,i,n),description:""})})),o.sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))},e._triggerGroups=(t,i,a,s,r)=>{if(!i||!a)return[];var o=[],n=new Set;return Object.keys(i).forEach((i=>{var l=(0,te.zz)(i);if(!n.has(l)){n.add(l);var c=a[l],h=!s||s.has(l);(void 0===r&&(Pe.has(l)||"entity"===(null==c?void 0:c.integration_type)&&h&&!Be.has(l))||"helper"===r&&"helper"===(null==c?void 0:c.integration_type)||"other"===r&&!Pe.has(l)&&(Be.has(l)||!h&&"entity"===(null==c?void 0:c.integration_type)||!["helper","entity"].includes((null==c?void 0:c.integration_type)||"")))&&o.push({icon:(0,m.qy)(de||(de=Ze`
            <ha-domain-icon
              .hass=${0}
              .domain=${0}
              brand-fallback
            ></ha-domain-icon>
          `),e.hass,l),key:`${W.VH}${l}`,name:(0,X.p$)(t,l,c),description:""})}})),o.sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))},e._triggers=(0,$.A)(((t,i,a)=>i?e._getTriggerListItems(t,Object.keys(i).filter((e=>{var t=(0,te.zz)(e);return!a||a===`${W.VH}${t}`}))):[])),e._conditionGroups=(t,i,a,s,r)=>{if(!i||!a)return[];var o=[],n=new Set;return Object.keys(i).forEach((i=>{var l=(0,K.ob)(i);if(!n.has(l)){n.add(l);var c=a[l],h=!s||s.has(l);(void 0===r&&(Pe.has(l)||"entity"===(null==c?void 0:c.integration_type)&&h&&!Be.has(l))||"helper"===r&&"helper"===(null==c?void 0:c.integration_type)||"other"===r&&!Pe.has(l)&&(Be.has(l)||!h&&"entity"===(null==c?void 0:c.integration_type)||!["helper","entity"].includes((null==c?void 0:c.integration_type)||"")))&&o.push({icon:(0,m.qy)(ue||(ue=Ze`
            <ha-domain-icon
              .hass=${0}
              .domain=${0}
              brand-fallback
            ></ha-domain-icon>
          `),e.hass,l),key:`${W.VH}${l}`,name:(0,X.p$)(t,l,c),description:""})}})),o.sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))},e._conditions=(0,$.A)(((t,i,a,s)=>{if(!i)return[];for(var r=[],o=0,n=Object.keys(i);o<n.length;o++){var l=n[o],c=(0,K.ob)(l);s&&s!==`${W.VH}${c}`||r.push(e._getConditionListItem(t,c,l))}return r})),e._services=(0,$.A)(((t,i,a,s)=>{if(!i)return[];var r,o=[];(0,W.Q)(s)&&(r=(0,W.Dt)(s));var n=a=>{for(var s=0,n=Object.keys(i[a]);s<n.length;s++){var l,c,h=n[s];o.push({icon:(0,m.qy)(ve||(ve=Ze`
              <ha-service-icon
                .hass=${0}
                .service=${0}
              ></ha-service-icon>
            `),e.hass,`${a}.${h}`),key:`${W.VH}${a}.${h}`,name:`${r?"":`${(0,X.p$)(t,a)}: `}${e.hass.localize(`component.${a}.services.${h}.name`,e.hass.services[a][h].description_placeholders)||(null===(l=i[a][h])||void 0===l?void 0:l.name)||h}`,description:e.hass.localize(`component.${a}.services.${h}.description`,e.hass.services[a][h].description_placeholders)||(null===(c=i[a][h])||void 0===c?void 0:c.description)||""})}};return r?(n(r),o.sort(((t,i)=>(0,M.xL)(t.name,i.name,e.hass.locale.language)))):s&&!["helpers","other"].includes(s)?[]:(Object.keys(i).sort().forEach((e=>{var t=null==a?void 0:a[e];"helpers"===s&&"helper"!==(null==t?void 0:t.integration_type)||"other"===s&&(Be.has(e)||["helper","entity"].includes((null==t?void 0:t.integration_type)||""))||n(e)})),o)})),e._getLabel=(0,$.A)((t=>{var i;return null===(i=e._labelRegistry)||void 0===i?void 0:i.find((e=>e.label_id===t))})),e._getFloorAreaLookupMemoized=(0,$.A)((e=>(0,J._o)(Object.values(e)))),e._getAreaDeviceLookupMemoized=(0,$.A)((e=>(0,P.QI)(Object.values(e)))),e._getAreaEntityLookupMemoized=(0,$.A)((e=>(0,P.bQ)(Object.values(e)))),e._getDeviceEntityLookupMemoized=(0,$.A)((e=>(0,R.I3)(Object.values(e)))),e._extractTypeAndIdFromTarget=(0,$.A)((e=>{var t=(0,l.A)(Object.entries(e)[0],2),i=t[0],a=t[1];return[i.replace("_id",""),a]})),e._convertToItem=(e,t,i,a)=>({key:e,name:a(`ui.panel.config.automation.editor.${i}s.${t.members?"groups":"type"}.${e}.label`),description:a(`ui.panel.config.automation.editor.${i}s.${t.members?"groups":"type"}.${e}.description${t.members?"":".picker"}`),iconPath:t.icon||Fe[i].icons[e]}),e._handleTargetSelected=t=>{e._targetItems=void 0,e._loadItemsError=!1,e._selectedTarget=t.detail.value,C.G.history.pushState({dialogData:{target:e._selectedTarget}},""),requestAnimationFrame((()=>{var t,i;e._narrow?null===(t=e._contentElement)||void 0===t||t.scrollTo(0,0):null===(i=e._itemsListElement)||void 0===i||i.scrollTo(0,0)})),e._getItemsByTarget()},e._debounceFilterChanged=(0,S.s)((t=>e._filterChanged(t)),200),e._filterChanged=t=>{e._filter=t.detail.value},e._addClipboard=()=>{var t;null!==(t=e._params)&&void 0!==t&&t.clipboardItem&&(e._params.add(le.u),(0,se.P)((0,d.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.item_pasted",{item:e.hass.localize(`ui.panel.config.automation.editor.${e._params.type}s.type.${e._params.clipboardItem}.label`)})}),e.closeDialog())},e._getSelectedTargetLabel=(0,$.A)((t=>{var i=e._extractTypeAndIdFromTarget(t),a=(0,l.A)(i,2),s=a[0],r=a[1];if(void 0===r&&"floor"===s)return e.hass.localize("ui.panel.config.automation.editor.other_areas");if(void 0===r&&"area"===s)return e.hass.localize("ui.panel.config.automation.editor.unassigned_devices");if(void 0===r&&"service"===s)return e.hass.localize("ui.panel.config.automation.editor.services");if(void 0===r&&"device"===s)return e.hass.localize("ui.panel.config.automation.editor.unassigned_entities");if(void 0===r&&"helper"===s)return e.hass.localize("ui.panel.config.automation.editor.helpers");if(void 0===r&&(s.startsWith("entity_")||s.startsWith("helper_"))){var o,n=s.substring(7);return(0,X.p$)(e.hass.localize,n,null===(o=e._manifests)||void 0===o?void 0:o[n])}if(r){if("floor"===s)return(0,L.X)(e.hass.floors[r])||r;if("area"===s)return(0,k.A)(e.hass.areas[r])||r;if("device"===s)return(0,V.xn)(e.hass.devices[r])||r;if("entity"===s&&e.hass.states[r]){var c=e.hass.states[r],h=(0,w.Cf)(c,[{type:"entity"},{type:"device"},{type:"area"}],e.hass.entities,e.hass.devices,e.hass.areas,e.hass.floors),d=(0,l.A)(h,2),u=d[0],v=d[1];return u||v||r}if("label"===s){var p=e._getLabel(r);return(null==p?void 0:p.name)||r}}})),e._getAddFromTargetHidden=(0,$.A)(((t,i)=>{if(t&&i){var a,s,r,o,n=e._extractTypeAndIdFromTarget(i),c=(0,l.A)(n,2),h=c[0],d=c[1];if(d&&("floor"===h&&!((null===(a=e._getFloorAreaLookupMemoized(e.hass.areas)[d])||void 0===a?void 0:a.length)>0)||"area"===h&&!((null===(s=e._getAreaDeviceLookupMemoized(e.hass.devices)[d])||void 0===s?void 0:s.length)>0)&&!((null===(r=e._getAreaEntityLookupMemoized(e.hass.entities)[d])||void 0===r?void 0:r.length)>0)||"device"===h&&!((null===(o=e._getDeviceEntityLookupMemoized(e.hass.entities)[d])||void 0===o?void 0:o.length)>0)||"entity"===h||"label"===h))return"hidden"}return""})),e}return(0,v.A)(t,e),(0,h.A)(t,[{key:"willUpdate",value:function(e){var t;e.has("hass")&&(null===(t=e.get("hass"))||void 0===t?void 0:t.states)!==this.hass.states&&this._calculateUsedDomains(),e.has("_newTriggersAndConditions")&&this._subscribeDescriptions()}},{key:"_subscribeDescriptions",value:function(){var e,t;this._unsubscribe(),"trigger"===(null===(e=this._params)||void 0===e?void 0:e.type)?(this._triggerDescriptions={},this._unsub=(0,te.Wv)(this.hass,(e=>{this._triggerDescriptions=Object.assign(Object.assign({},this._triggerDescriptions),e)}))):"condition"===(null===(t=this._params)||void 0===t?void 0:t.type)&&(this._conditionDescriptions={},this._unsub=(0,K.bn)(this.hass,(e=>{this._conditionDescriptions=Object.assign(Object.assign({},this._conditionDescriptions),e)})))}},{key:"showDialog",value:function(e){var t,i,a;this._params=e,this.addKeyboardShortcuts(),this._loadConfigEntries(),this._unsubscribe(),this._fetchManifests(),this._calculateUsedDomains(),this._unsubscribeLabFeatures=(0,Y.CO)(this.hass.connection,"automation","new_triggers_conditions",(e=>{this._newTriggersAndConditions=e.enabled,this._tab=this._newTriggersAndConditions?"targets":"groups"})),C.G.history.pushState({dialogData:{}},""),"action"===(null===(t=this._params)||void 0===t?void 0:t.type)?(this.hass.loadBackendTranslation("services"),(0,Q.Yd)(this.hass)):"trigger"===(null===(i=this._params)||void 0===i?void 0:i.type)?(this.hass.loadBackendTranslation("triggers"),(0,Q.Dl)(this.hass),this._subscribeDescriptions()):"condition"===(null===(a=this._params)||void 0===a?void 0:a.type)&&(this.hass.loadBackendTranslation("conditions"),(0,Q.mX)(this.hass),this._subscribeDescriptions()),window.addEventListener("resize",this._updateNarrow),this._updateNarrow(),this._bottomSheetMode=this._narrow}},{key:"closeDialog",value:function(e){var t;if(this._open&&e&&(this._selectedTarget||this._selectedGroup)){var i,a;if(null!==(i=e.dialogData)&&void 0!==i&&i.target)return this._selectedTarget=e.dialogData.target,this._getItemsByTarget(),this._tab="targets",!1;if(null!==(a=e.dialogData)&&void 0!==a&&a.group)return this._selectedCollectionIndex=e.dialogData.collectionIndex,this._selectedGroup=e.dialogData.group,this._tab="groups",!1;if(this._narrow)return this._selectedTarget=void 0,this._selectedGroup=void 0,!1}return null!==(t=C.G.history.state)&&void 0!==t&&t.dialogData?(this._open=!1,C.G.history.back(),!1):(this.removeKeyboardShortcuts(),this._unsubscribe(),this._params&&(0,A.r)(this,"dialog-closed",{dialog:this.localName}),this._open=!0,this._params=void 0,this._selectedCollectionIndex=void 0,this._selectedGroup=void 0,this._selectedTarget=void 0,this._tab=this._newTriggersAndConditions?"targets":"groups",this._filter="",this._manifests=void 0,this._domains=void 0,this._bottomSheetMode=!1,this._narrow=!1,this._targetItems=void 0,this._loadItemsError=!1,!0)}},{key:"_calculateUsedDomains",value:function(){var e=new Set(Object.keys(this.hass.states).map(H.m));(0,I.b)(e,this._domains)||(this._domains=e)}},{key:"_loadConfigEntries",value:(_=(0,o.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,N.VN)(this.hass);case 1:t=e.v,this._configEntryLookup=Object.fromEntries(t.map((e=>[e.entry_id,e])));case 2:return e.a(2)}}),e,this)}))),function(){return _.apply(this,arguments)})},{key:"_fetchManifests",value:(a=(0,o.A)((0,r.A)().m((function e(){var t,i,a,o,n;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return t={},e.n=1,(0,X.fK)(this.hass);case 1:i=e.v,a=(0,s.A)(i);try{for(a.s();!(o=a.n()).done;)n=o.value,t[n.domain]=n}catch(r){a.e(r)}finally{a.f()}this._manifests=t;case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"disconnectedCallback",value:function(){(0,p.A)(t,"disconnectedCallback",this,3)([]),window.removeEventListener("resize",this._updateNarrow),this._unsubscribe()}},{key:"supportedShortcuts",value:function(){return{v:()=>this._addClipboard()}}},{key:"_unsubscribe",value:function(){this._unsub&&(this._unsub.then((e=>e())),this._unsub=void 0),this._unsubscribeLabFeatures&&(this._unsubscribeLabFeatures.then((e=>e())),this._unsubscribeLabFeatures=void 0)}},{key:"render",value:function(){return this._params?this._bottomSheetMode?(0,m.qy)(pe||(pe=Ze`
        <ha-bottom-sheet
          .open=${0}
          @closed=${0}
          flexcontent
        >
          ${0}
        </ha-bottom-sheet>
      `),this._open,this._handleClosed,this._renderContent()):(0,m.qy)(_e||(_e=Ze`
      <ha-wa-dialog
        width="large"
        .open=${0}
        @closed=${0}
        flexcontent
      >
        ${0}
      </ha-wa-dialog>
    `),this._open,this._handleClosed,this._renderContent()):m.s6}},{key:"_renderContent",value:function(){var e,t=this._params.type,i=[{label:this.hass.localize(`ui.panel.config.automation.editor.${t}s.name`),value:"groups"}];this._newTriggersAndConditions&&i.unshift({label:this.hass.localize("ui.panel.config.automation.editor.targets"),value:"targets"}),"trigger"!==(null===(e=this._params)||void 0===e?void 0:e.type)&&i.push({label:this.hass.localize("ui.panel.config.automation.editor.blocks"),value:"blocks"});var a=this._filter||"blocks"===this._tab||"targets"===this._tab||this._narrow&&this._selectedGroup,s=a?[]:this._getCollections(t,Fe[t].collections,this._domains,this.hass.localize,this.hass.services,this._triggerDescriptions,this._conditionDescriptions,this._manifests);return(0,m.qy)(ge||(ge=Ze`
      <div slot="header">
        ${0}
        ${0}
        ${0}
      </div>
      <div
        class=${0}
      >
        ${0}
        ${0}
      </div>
    `),this._renderHeader(),this._narrow&&(this._selectedGroup||this._selectedTarget)?m.s6:(0,m.qy)(me||(me=Ze`
              <search-input
                ?autofocus=${0}
                .hass=${0}
                .filter=${0}
                @value-changed=${0}
                .label=${0}
              ></search-input>
            `),!this._narrow,this.hass,this._filter,this._debounceFilterChanged,this.hass.localize("ui.common.search")),this._filter||!(i.length>1)||this._narrow&&(this._selectedGroup||this._selectedTarget)?m.s6:(0,m.qy)(fe||(fe=Ze`<ha-button-toggle-group
              variant="neutral"
              active-variant="brand"
              .buttons=${0}
              .active=${0}
              size="small"
              full-width
              @value-changed=${0}
            ></ha-button-toggle-group>`),i,this._tab,this._switchTab),(0,y.H)({content:!0,column:this._filter||this._narrow&&this._selectedTarget&&Object.values(this._selectedTarget)[0]&&!this._getAddFromTargetHidden(this._narrow,this._selectedTarget)}),this._filter?(0,m.qy)(ye||(ye=Ze`<ha-automation-add-search
              .hass=${0}
              .filter=${0}
              .configEntryLookup=${0}
              .manifests=${0}
              .narrow=${0}
              .addElementType=${0}
              .items=${0}
              .convertToItem=${0}
              .newTriggersAndConditions=${0}
              @search-element-picked=${0}
            >
            </ha-automation-add-search>`),this.hass,this._filter,this._configEntryLookup,this._manifests,this._narrow,this._params.type,this._items(t,this.hass.localize,this.hass.services,this._manifests),this._convertToItem,this._newTriggersAndConditions,this._searchItemSelected):"targets"===this._tab?(0,m.qy)(be||(be=Ze`<ha-automation-add-from-target
                .hass=${0}
                .value=${0}
                @value-changed=${0}
                .narrow=${0}
                class=${0}
                .manifests=${0}
              ></ha-automation-add-from-target>`),this.hass,this._selectedTarget,this._handleTargetSelected,this._narrow,this._getAddFromTargetHidden(this._narrow,this._selectedTarget),this._manifests):(0,m.qy)($e||($e=Ze`
                <ha-md-list
                  class=${0}
                >
                  ${0}
                  ${0}
                </ha-md-list>
              `),(0,y.H)({groups:!0,hidden:a}),this._params.clipboardItem?(0,m.qy)(Ae||(Ae=Ze`<ha-md-list-item
                          interactive
                          type="button"
                          class="paste"
                          @click=${0}
                        >
                          <div class="shortcut-label">
                            <div class="label">
                              <div>
                                ${0}
                              </div>
                              <div class="supporting-text">
                                ${0}
                              </div>
                            </div>
                            ${0}
                          </div>
                          <ha-svg-icon
                            slot="start"
                            .path=${0}
                          ></ha-svg-icon
                          ><ha-svg-icon
                            class="plus"
                            slot="end"
                            .path=${0}
                          ></ha-svg-icon>
                        </ha-md-list-item>
                        <ha-md-divider
                          role="separator"
                          tabindex="-1"
                        ></ha-md-divider>`),this._paste,this.hass.localize(`ui.panel.config.automation.editor.${t}s.paste`),this.hass.localize(`ui.panel.config.automation.editor.${t}s.type.${this._params.clipboardItem}.label`),this._narrow?m.s6:(0,m.qy)(Ce||(Ce=Ze`<span class="shortcut">
                                  <span
                                    >${0}</span
                                  >
                                  <span>+</span>
                                  <span>V</span>
                                </span>`),ae.c?(0,m.qy)(ke||(ke=Ze`<ha-svg-icon
                                          slot="start"
                                          .path=${0}
                                        ></ha-svg-icon>`),"M6,2A4,4 0 0,1 10,6V8H14V6A4,4 0 0,1 18,2A4,4 0 0,1 22,6A4,4 0 0,1 18,10H16V14H18A4,4 0 0,1 22,18A4,4 0 0,1 18,22A4,4 0 0,1 14,18V16H10V18A4,4 0 0,1 6,22A4,4 0 0,1 2,18A4,4 0 0,1 6,14H8V10H6A4,4 0 0,1 2,6A4,4 0 0,1 6,2M16,18A2,2 0 0,0 18,20A2,2 0 0,0 20,18A2,2 0 0,0 18,16H16V18M14,10H10V14H14V10M6,16A2,2 0 0,0 4,18A2,2 0 0,0 6,20A2,2 0 0,0 8,18V16H6M8,6A2,2 0 0,0 6,4A2,2 0 0,0 4,6A2,2 0 0,0 6,8H8V6M18,8A2,2 0 0,0 20,6A2,2 0 0,0 18,4A2,2 0 0,0 16,6V8H18Z"):this.hass.localize("ui.panel.config.automation.editor.ctrl")),"M19,20H5V4H7V7H17V4H19M12,2A1,1 0 0,1 13,3A1,1 0 0,1 12,4A1,1 0 0,1 11,3A1,1 0 0,1 12,2M19,2H14.82C14.4,0.84 13.3,0 12,0C10.7,0 9.6,0.84 9.18,2H5A2,2 0 0,0 3,4V20A2,2 0 0,0 5,22H19A2,2 0 0,0 21,20V4A2,2 0 0,0 19,2Z","M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"):m.s6,s.map(((e,t)=>(0,m.qy)(Ve||(Ve=Ze`
                      ${0}
                      ${0}
                    `),e.titleKey&&e.groups.length?(0,m.qy)(He||(He=Ze`<ha-section-title>
                            ${0}
                          </ha-section-title>`),this.hass.localize(e.titleKey)):m.s6,(0,b.u)(e.groups,(e=>e.key),(e=>(0,m.qy)(we||(we=Ze`
                          <ha-md-list-item
                            interactive
                            type="button"
                            .value=${0}
                            .index=${0}
                            @click=${0}
                            class=${0}
                          >
                            <div slot="headline">${0}</div>
                            ${0}
                            ${0}
                          </ha-md-list-item>
                        `),e.key,t,this._groupSelected,e.key===this._selectedGroup?"selected":"",e.name,e.icon?(0,m.qy)(Le||(Le=Ze`<span slot="start">${0}</span>`),e.icon):e.iconPath?(0,m.qy)(Me||(Me=Ze`<ha-svg-icon
                                    slot="start"
                                    .path=${0}
                                  ></ha-svg-icon>`),e.iconPath):m.s6,this._narrow?(0,m.qy)(xe||(xe=Ze`<ha-icon-next slot="end"></ha-icon-next>`)):m.s6))))))),this._filter?m.s6:(0,m.qy)(Se||(Se=Ze`
              <ha-automation-add-items
                .hass=${0}
                .items=${0}
                .scrollable=${0}
                .error=${0}
                .selectLabel=${0}
                .emptyLabel=${0}
                .tooltipDescription=${0}
                .target=${0}
                .getLabel=${0}
                .configEntryLookup=${0}
                class=${0}
                @value-changed=${0}
              >
              </ha-automation-add-items>
            `),this.hass,this._getItems(),!this._narrow,"targets"===this._tab&&this._loadItemsError?this.hass.localize("ui.panel.config.automation.editor.load_target_items_failed"):void 0,this.hass.localize("ui.panel.config.automation.editor."+("groups"===this._tab?`${t}s.select`:"select_target")),this.hass.localize(`ui.panel.config.automation.editor.${t}s.no_items_for_target`),"targets"===this._tab,"targets"===this._tab&&this._selectedTarget&&[].concat((0,n.A)(this._extractTypeAndIdFromTarget(this._selectedTarget)),[this._getSelectedTargetLabel(this._selectedTarget)])||void 0,this._getLabel,this._configEntryLookup,!this._narrow||this._selectedGroup||this._selectedTarget&&(!this._selectedTarget||Object.values(this._selectedTarget)[0])||"blocks"===this._tab?"":"hidden",this._selected))}},{key:"_renderHeader",value:function(){return(0,m.qy)(Ie||(Ie=Ze`
      <ha-dialog-header subtitle-position="above">
        <span slot="title">${0}</span>

        ${0}
        ${0}
      </ha-dialog-header>
    `),this._getDialogTitle(),this._renderDialogSubtitle(),this._narrow&&(this._selectedGroup||this._selectedTarget)?(0,m.qy)(Oe||(Oe=Ze`<ha-icon-button-prev
              slot="navigationIcon"
              @click=${0}
            ></ha-icon-button-prev>`),this._back):(0,m.qy)(je||(je=Ze`<ha-icon-button
              .path=${0}
              @click=${0}
              slot="navigationIcon"
            ></ha-icon-button>`),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",this._close))}},{key:"_renderDialogSubtitle",value:function(){if(!this._narrow)return m.s6;if(this._selectedGroup)return(0,m.qy)(ze||(ze=Ze`<span slot="subtitle"
        >${0}</span
      >`),this.hass.localize(`ui.panel.config.automation.editor.${this._params.type}s.add`));if(this._selectedTarget){var e,t=this._extractTypeAndIdFromTarget(this._selectedTarget),i=(0,l.A)(t,2),a=i[0],s=i[1];if(s){if("area"===a){var r,o=null===(r=this.hass.areas[s])||void 0===r?void 0:r.floor_id;e=o?(0,L.X)(this.hass.floors[o])||o:this.hass.localize("ui.panel.config.automation.editor.other_areas")}else if("device"===a){var n,c=null===(n=this.hass.devices[s])||void 0===n?void 0:n.area_id;if(c)e=(0,k.A)(this.hass.areas[c])||c;else{var h=this.hass.devices[s];e=this.hass.localize("ui.panel.config.automation.editor."+("service"===(null==h?void 0:h.entry_type)?"services":"unassigned_devices"))}}else if("entity"===a&&this.hass.states[s]){var d=this.hass.entities[s];if(!d||d.device_id||d.area_id){var u=this.hass.states[s],v=(0,w.Cf)(u,[{type:"entity"},{type:"device"},{type:"area"}],this.hass.entities,this.hass.devices,this.hass.areas,this.hass.floors),p=(0,l.A)(v,3),_=p[0],g=p[1];e=[p[2],_?g:void 0].filter(Boolean).join((0,x.qC)(this.hass)?" ◂ ":" ▸ ")}else{var f,y=s.split(".",2)[0];e=(0,X.p$)(this.hass.localize,y,null===(f=this._manifests)||void 0===f?void 0:f[y])}}if(e)return(0,m.qy)(Ge||(Ge=Ze`<span slot="subtitle">${0}</span>`),e)}}return m.s6}},{key:"_getDomainType",value:function(e){var t,i;return Pe.has(e)||"entity"===(null===(t=this._manifests)||void 0===t?void 0:t[e].integration_type)&&!Be.has(e)?"dynamicGroups":"helper"===(null===(i=this._manifests)||void 0===i?void 0:i[e].integration_type)?"helpers":"other"}},{key:"_sortDomainsByCollection",value:function(e,t){var i=[];return Fe[e].collections.forEach((e=>{i.push.apply(i,(0,n.A)(Object.keys(e.groups)))})),t.sort(((e,t)=>{var a=e[0],s=t[0];if(i.includes(a)&&i.includes(s))return i.indexOf(a)-i.indexOf(s);var r=a,o=s;return i.includes(a)||(r=this._getDomainType(a)),i.includes(s)||(o=this._getDomainType(s)),r===o?(0,M.xL)(e[1].title,t[1].title,this.hass.locale.language):i.indexOf(r)-i.indexOf(o)})).map((e=>e[1]))}},{key:"_getDomainGroupedTriggerListItems",value:function(e,t){var i={};return t.forEach((t=>{var a,s=(0,te.zz)(t);i[s]||(i[s]={title:(0,X.p$)(e,s,null===(a=this._manifests)||void 0===a?void 0:a[s]),items:[]});i[s].items.push(this._getTriggerListItem(e,s,t)),i[s].items.sort(((e,t)=>(0,M.xL)(e.name,t.name,this.hass.locale.language)))})),this._sortDomainsByCollection(this._params.type,Object.entries(i))}},{key:"_getTriggerListItems",value:function(e,t){return t.map((t=>{var i=(0,te.zz)(t);return this._getTriggerListItem(e,i,t)})).sort(((e,t)=>(0,M.xL)(e.name,t.name,this.hass.locale.language)))}},{key:"_getTriggerListItem",value:function(e,t,i){var a=(0,te.hN)(i);return{icon:(0,m.qy)(Te||(Te=Ze`
        <ha-trigger-icon
          .hass=${0}
          .trigger=${0}
        ></ha-trigger-icon>
      `),this.hass,i),key:`${W.VH}${i}`,name:e(`component.${t}.triggers.${a}.name`)||i,description:e(`component.${t}.triggers.${a}.description`)||i}}},{key:"_getConditionListItem",value:function(e,t,i){var a=(0,K.YQ)(i);return{icon:(0,m.qy)(qe||(qe=Ze`
        <ha-condition-icon
          .hass=${0}
          .condition=${0}
        ></ha-condition-icon>
      `),this.hass,i),key:`${W.VH}${i}`,name:e(`component.${t}.conditions.${a}.name`)||i,description:e(`component.${t}.conditions.${a}.description`)||i}}},{key:"_getDomainGroupedActionListItems",value:function(e,t){var i={};return t.forEach((t=>{var a,s,r,o=t.split(".",2),n=(0,l.A)(o,2),c=n[0],h=n[1];i[c]||(i[c]={title:(0,X.p$)(e,c,null===(r=this._manifests)||void 0===r?void 0:r[c]),items:[]});i[c].items.push({icon:(0,m.qy)(Ee||(Ee=Ze`
          <ha-service-icon
            .hass=${0}
            .service=${0}
          ></ha-service-icon>
        `),this.hass,`${c}.${h}`),key:`${W.VH}${c}.${h}`,name:`${c?"":`${(0,X.p$)(e,c)}: `}${this.hass.localize(`component.${c}.services.${h}.name`)||(null===(a=this.hass.services[c][h])||void 0===a?void 0:a.name)||h}`,description:this.hass.localize(`component.${c}.services.${h}.description`)||(null===(s=this.hass.services[c][h])||void 0===s?void 0:s.description)||""}),i[c].items.sort(((e,t)=>(0,M.xL)(e.name,t.name,this.hass.locale.language)))})),this._sortDomainsByCollection(this._params.type,Object.entries(i))}},{key:"_getDomainGroupedConditionListItems",value:function(e,t){var i={};return t.forEach((t=>{var a,s=(0,K.ob)(t);i[s]||(i[s]={title:(0,X.p$)(e,s,null===(a=this._manifests)||void 0===a?void 0:a[s]),items:[]});i[s].items.push(this._getConditionListItem(e,s,t)),i[s].items.sort(((e,t)=>(0,M.xL)(e.name,t.name,this.hass.locale.language)))})),this._sortDomainsByCollection(this._params.type,Object.entries(i))}},{key:"_close",value:function(){this._open=!1}},{key:"_back",value:function(){C.G.history.back()}},{key:"_groupSelected",value:function(e){var t=e.currentTarget;if(this._selectedGroup===t.value)return this._selectedGroup=void 0,void(this._selectedCollectionIndex=void 0);this._selectedGroup=t.value,this._selectedCollectionIndex=e.currentTarget.index,C.G.history.pushState({dialogData:{group:this._selectedGroup,collectionIndex:this._selectedCollectionIndex}},""),requestAnimationFrame((()=>{var e;null===(e=this._itemsListElement)||void 0===e||e.scrollTo(0,0)}))}},{key:"_paste",value:function(){this._params.add(le.u),this.closeDialog()}},{key:"_selected",value:function(e){var t;"targets"===this._tab&&this._selectedTarget&&Object.values(this._selectedTarget)[0]&&(t=this._selectedTarget),this._params.add(e.detail.value,t),this.closeDialog()}},{key:"_getItemsByTarget",value:(i=(0,o.A)((0,r.A)().m((function e(){var t,i,a,s,o;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(this._selectedTarget){e.n=1;break}return e.a(2);case 1:if(e.p=1,"trigger"!==this._params.type){e.n=3;break}return e.n=2,(0,ee.oV)(this.hass.callWS,this._selectedTarget);case 2:return t=e.v,this._targetItems=this._getDomainGroupedTriggerListItems(this.hass.localize,t),e.a(2);case 3:if("condition"!==this._params.type){e.n=5;break}return e.n=4,(0,ee.vN)(this.hass.callWS,this._selectedTarget);case 4:return i=e.v,this._targetItems=this._getDomainGroupedConditionListItems(this.hass.localize,i),e.a(2);case 5:if("action"!==this._params.type){e.n=7;break}return e.n=6,(0,ee.j_)(this.hass.callWS,this._selectedTarget);case 6:a=e.v,s=a.filter((e=>!e.startsWith("homeassistant."))),this._targetItems=this._getDomainGroupedActionListItems(this.hass.localize,s);case 7:e.n=9;break;case 8:e.p=8,o=e.v,this._loadItemsError=!0,console.error(`Error fetching ${this._params.type}s for target`,o);case 9:return e.a(2)}}),e,this,[[1,8]])}))),function(){return i.apply(this,arguments)})},{key:"_switchTab",value:function(e){this._tab=e.detail.value}},{key:"_searchItemSelected",value:function(e){var t=e.detail;if(t.type&&!["floor","area"].includes(t.type))return this._params.add(t.id),void this.closeDialog();var i=(0,ee.OJ)(t);this._filter="",this._selectedTarget={[`${i}_id`]:t.id.split(ee.G_,2)[1]},this._tab="targets"}},{key:"_handleClosed",value:function(){this.closeDialog()}},{key:"_getDialogTitle",value:function(){var e;if(this._narrow&&this._selectedGroup)return(0,W.Q)(this._selectedGroup)?(0,X.p$)(this.hass.localize,(0,W.Dt)(this._selectedGroup),null===(e=this._manifests)||void 0===e?void 0:e[(0,W.Dt)(this._selectedGroup)]):this.hass.localize(`ui.panel.config.automation.editor.${this._params.type}s.groups.${this._selectedGroup}.label`)||this.hass.localize(`ui.panel.config.automation.editor.${this._params.type}s.type.${this._selectedGroup}.label`);if(this._narrow&&this._selectedTarget){var t=this._getSelectedTargetLabel(this._selectedTarget);if(t)return t}return this.hass.localize(`ui.panel.config.automation.editor.${this._params.type}s.add`)}}],[{key:"styles",get:function(){return[(0,m.AH)(De||(De=Ze`
        ha-bottom-sheet {
          --ha-bottom-sheet-height: 90vh;
          --ha-bottom-sheet-height: calc(100dvh - var(--ha-space-12));
          --ha-bottom-sheet-max-height: var(--ha-bottom-sheet-height);
          --ha-bottom-sheet-max-width: 888px;
          --ha-bottom-sheet-padding: var(--ha-space-0);
          --ha-bottom-sheet-surface-background: var(--card-background-color);
        }

        ha-wa-dialog {
          --dialog-content-padding: var(--ha-space-0);
          --ha-dialog-min-height: min(
            800px,
            calc(
              100vh - max(
                  var(--safe-area-inset-bottom),
                  var(--ha-space-4)
                ) - max(var(--safe-area-inset-top), var(--ha-space-4))
            )
          );
          --ha-dialog-min-height: min(
            800px,
            calc(
              100dvh - max(
                  var(--safe-area-inset-bottom),
                  var(--ha-space-4)
                ) - max(var(--safe-area-inset-top), var(--ha-space-4))
            )
          );
          --ha-dialog-max-height: var(--ha-dialog-min-height);
        }

        search-input {
          display: block;
          margin: var(--ha-space-0) var(--ha-space-4);
        }

        ha-button-toggle-group {
          --ha-button-toggle-group-padding: var(--ha-space-3) var(--ha-space-4)
            0;
        }

        .content {
          flex: 1;
          min-height: 0;
          height: 100%;
          display: flex;
        }

        .content.column {
          flex-direction: column;
        }

        ha-md-list {
          padding: 0;
        }

        ha-automation-add-from-target,
        .groups {
          border-radius: var(--ha-border-radius-xl);
          border: 1px solid var(--ha-color-border-neutral-quiet);
          margin: var(--ha-space-3);
        }

        ha-automation-add-from-target,
        .groups {
          overflow: auto;
          flex: 4;
          margin-inline-end: var(--ha-space-0);
        }

        ha-automation-add-from-target.hidden {
          display: none;
        }

        .groups {
          --md-list-item-leading-space: var(--ha-space-3);
          --md-list-item-trailing-space: var(--md-list-item-leading-space);
          --md-list-item-bottom-space: var(--ha-space-1);
          --md-list-item-top-space: var(--md-list-item-bottom-space);
          --md-list-item-supporting-text-font: var(--ha-font-family-body);
          --md-list-item-one-line-container-height: var(--ha-space-10);
        }
        ha-bottom-sheet .groups,
        ha-bottom-sheet ha-automation-add-from-target {
          margin: var(--ha-space-3);
        }
        .groups .selected {
          background-color: var(--ha-color-fill-primary-normal-active);
          --md-list-item-label-text-color: var(--ha-color-on-primary-normal);
          --icon-primary-color: var(--ha-color-on-primary-normal);
        }
        .groups .selected ha-svg-icon {
          color: var(--ha-color-on-primary-normal);
        }

        ha-section-title {
          top: 0;
          position: sticky;
          z-index: 1;
        }

        ha-automation-add-items {
          flex: 6;
        }

        .content.column ha-automation-add-from-target,
        .content.column ha-automation-add-items {
          flex: none;
        }
        .content.column ha-automation-add-items {
          min-height: 160px;
        }
        .content.column ha-automation-add-from-target {
          overflow: clip;
        }

        ha-wa-dialog ha-automation-add-items {
          margin-top: var(--ha-space-3);
        }

        ha-bottom-sheet .groups {
          padding-bottom: max(var(--safe-area-inset-bottom), var(--ha-space-4));
        }

        ha-automation-add-items.hidden,
        .groups.hidden {
          display: none;
        }

        .groups {
          padding-bottom: max(var(--safe-area-inset-bottom), var(--ha-space-3));
        }

        ha-icon-next {
          width: var(--ha-space-6);
        }

        ha-md-list-item.paste {
          border-bottom: 1px solid var(--ha-color-border-neutral-quiet);
        }

        ha-svg-icon.plus {
          color: var(--primary-color);
        }
        .shortcut-label {
          display: flex;
          gap: var(--ha-space-3);
          justify-content: space-between;
        }
        .shortcut-label .supporting-text {
          color: var(--secondary-text-color);
          font-size: var(--ha-font-size-s);
        }
        .shortcut-label .shortcut {
          --mdc-icon-size: var(--ha-space-3);
          display: inline-flex;
          flex-direction: row;
          align-items: center;
          gap: 2px;
        }
        .shortcut-label .shortcut span {
          font-size: var(--ha-font-size-s);
          font-family: var(--ha-font-family-code);
          color: var(--ha-color-text-secondary);
        }

        .section-title-wrapper {
          height: 0;
          position: relative;
        }

        .section-title-wrapper ha-section-title {
          position: absolute;
          top: 0;
          width: calc(100% - var(--ha-space-4));
          z-index: 1;
        }

        ha-automation-add-search {
          flex: 1;
        }
      `))]}}]);var i,a,_}((0,ie.b)(m.WF));(0,_.__decorate)([(0,f.MZ)({attribute:!1})],Ke.prototype,"hass",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_open",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_params",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_selectedCollectionIndex",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_selectedGroup",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_selectedTarget",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_tab",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_filter",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_manifests",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_domains",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_bottomSheetMode",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_narrow",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_triggerDescriptions",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_targetItems",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_loadItemsError",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_newTriggersAndConditions",void 0),(0,_.__decorate)([(0,f.wk)()],Ke.prototype,"_conditionDescriptions",void 0),(0,_.__decorate)([(0,f.wk)(),(0,g.Fg)({context:U.HD,subscribe:!0})],Ke.prototype,"_labelRegistry",void 0),(0,_.__decorate)([(0,f.P)("ha-automation-add-items")],Ke.prototype,"_itemsListElement",void 0),(0,_.__decorate)([(0,f.P)(".content")],Ke.prototype,"_contentElement",void 0),Ke=(0,_.__decorate)([(0,f.EM)("add-automation-element-dialog")],Ke),a()}catch(Ne){a(Ne)}}))},90840:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),s=i(50264),r=i(78261),o=i(44734),n=i(56038),l=i(69683),c=i(6454),h=i(25460),d=(i(28706),i(2008),i(23792),i(62062),i(44114),i(26910),i(18111),i(22489),i(7588),i(61701),i(5506),i(53921),i(26099),i(16034),i(27495),i(25440),i(90744),i(23500),i(62826)),u=i(99222),v=i(73984),p=i(16527),_=i(96196),g=i(77845),m=i(32288),f=i(22786),y=i(92542),b=i(56403),$=i(16727),A=i(79384),C=i(25749),k=i(91720),V=(i(26537),i(22598),i(28608),i(42921),i(23897),i(12109),i(60961),i(45494)),H=i(54110),w=i(3950),L=i(34972),M=i(1491),x=i(84125),S=i(41327),I=i(6098),O=i(76681),j=e([u,v,k]);[u,v,k]=j.then?(await j)():j;var z,G,T,q,E,D,Z,F,B,P,W,K,N,U,R,J,Q,X,Y,ee,te,ie,ae,se,re,oe,ne,le,ce,he,de,ue=e=>e,ve="M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z",pe=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,l.A)(this,t,[].concat(a))).narrow=!1,e._floorAreas=[],e._entries={},e._fullHeight=!1,e._configEntryLookup={},e._renderNarrow=(0,f.A)(((t,i)=>{var a=(0,r.A)(Object.entries(i)[0],2),s=a[0],o=a[1],n=s.replace("_id","");if(!n||"label"===n)return _.s6;if("floor"===n)return e._renderAreas(t[`floor${I.G_}${null!=o?o:""}`].areas);if("area"===n&&o){var l,c=t[`floor${I.G_}${(null===(l=e.areas[o])||void 0===l?void 0:l.floor_id)||""}`].areas[`area${I.G_}${o}`],h=c.devices,d=c.entities,u=Object.keys(h).length;return(0,_.qy)(z||(z=ue`
          ${0}
          ${0}
        `),u?e._renderDevices(h):_.s6,d.length?e._renderEntities(d):_.s6)}if(!o&&"area"===n||"service"===n){var v=t[`${n}${I.G_}`].devices;return e._renderDevices(v)}if(o&&"device"===n){var p,g=null===(p=e.devices[o])||void 0===p?void 0:p.area_id;if(g){var m,f=(null===(m=e.areas[g])||void 0===m?void 0:m.floor_id)||"",y=t[`floor${I.G_}${f}`].areas[`area${I.G_}${g}`].devices[o].entities;return y.length?e._renderEntities(y):_.s6}var b=t[`${"service"===e.devices[o].entry_type?"service":"area"}${I.G_}`].devices[o].entities;return b.length?e._renderEntities(b):_.s6}if("device"===n||"helper"===n){var $=t[`${n}${I.G_}`].devices;return e._renderDomains($,"device"===n?"entity_":"helper_")}if(!o&&(n.startsWith("entity")||n.startsWith("helper"))){var A=t[`${n.startsWith("entity")?"device":"helper"}${I.G_}`].devices[`${n}${I.G_}`].entities;return e._renderEntities(A)}return _.s6})),e._renderFloors=(0,f.A)(((t,i,a)=>{var s=!e._floorAreas.length||!e._floorAreas[0].id&&!e._floorAreas[0].areas.length,r=s?void 0:e._floorAreas.map(((t,s)=>0!==s||t.id?e._renderItem(t.id?t.primary:e.localize("ui.panel.config.automation.editor.other_areas"),t.id||`floor${I.G_}`,!t.id,!!t.id&&e._getSelectedTargetId(a)===t.id,!i[t.id||`floor${I.G_}`].open&&!!Object.keys(i[t.id||`floor${I.G_}`].areas).length,i[t.id||`floor${I.G_}`].open,e._renderFloorIcon(t),i[t.id||`floor${I.G_}`].open?e._renderAreas(i[t.id||`floor${I.G_}`].areas):void 0):e._renderAreas(i[t.id||`floor${I.G_}`].areas)));return(0,_.qy)(G||(G=ue`<ha-section-title
          >${0}</ha-section-title
        >
        ${0}`),e.localize("ui.panel.config.automation.editor.home"),s?(0,_.qy)(T||(T=ue`<ha-md-list>
              <ha-md-list-item type="text">
                <div slot="headline">
                  ${0}
                </div>
              </ha-md-list-item>
            </ha-md-list>`),e.localize("ui.components.area-picker.no_areas")):(0,_.qy)(q||(q=ue`${0}`),t?(0,_.qy)(E||(E=ue`<ha-md-list>${0}</ha-md-list>`),r):(0,_.qy)(D||(D=ue`<wa-tree
                  @wa-selection-change=${0}
                  >${0}</wa-tree
                >`),e._handleSelectionChange,r)))})),e._renderLabels=(0,f.A)(((t,i)=>{var a=e._getLabelsMemoized(e.states,e.areas,e.devices,e.entities,e._labelRegistry,void 0,void 0,void 0,void 0,void 0,void 0,`label${I.G_}`);return a.length?(0,_.qy)(Z||(Z=ue`<ha-section-title
          >${0}</ha-section-title
        >
        <ha-md-list>
          ${0}
        </ha-md-list>`),e.localize("ui.components.label-picker.labels"),a.map((a=>(0,_.qy)(F||(F=ue`<ha-md-list-item
                interactive
                type="button"
                .target=${0}
                @click=${0}
                class=${0}
                >${0}
                <div slot="headline">${0}</div>
                ${0}
              </ha-md-list-item>`),a.id,e._selectItem,e._getSelectedTargetId(i)===a.id?"selected":"",a.icon?(0,_.qy)(B||(B=ue`<ha-icon slot="start" .icon=${0}></ha-icon>`),a.icon):a.icon_path?(0,_.qy)(P||(P=ue`<ha-svg-icon
                        slot="start"
                        .path=${0}
                      ></ha-svg-icon>`),a.icon_path):_.s6,a.primary,t?(0,_.qy)(W||(W=ue`<ha-icon-next slot="end"></ha-icon-next> `)):_.s6)))):_.s6})),e._renderUnassigned=(0,f.A)(((t,i,a)=>{var s,r,o,n,l=Object.keys((null===(s=i[`area${I.G_}`])||void 0===s?void 0:s.devices)||{}).length,c=Object.keys((null===(r=i[`service${I.G_}`])||void 0===r?void 0:r.devices)||{}).length,h=Object.keys((null===(o=i[`device${I.G_}`])||void 0===o?void 0:o.devices)||{}).length,d=Object.keys((null===(n=i[`helper${I.G_}`])||void 0===n?void 0:n.devices)||{}).length;if(!(l||c||h||d))return _.s6;var u=[];if(h){var v=i[`device${I.G_}`].open;u.push(e._renderItem(e.localize("ui.components.target-picker.type.entities"),`device${I.G_}`,!0,!1,!v,v,void 0,i[`device${I.G_}`].open?e._renderDomains(i[`device${I.G_}`].devices,"entity_"):void 0))}if(d){var p=i[`helper${I.G_}`].open;u.push(e._renderItem(e.localize("ui.panel.config.automation.editor.helpers"),`helper${I.G_}`,!0,!1,!p,p,void 0,i[`helper${I.G_}`].open?e._renderDomains(i[`helper${I.G_}`].devices,"helper_"):void 0))}if(l){var g=i[`area${I.G_}`].open;u.push(e._renderItem(e.localize("ui.components.target-picker.type.devices"),`area${I.G_}`,!0,!1,!g,g,void 0,i[`area${I.G_}`].open?e._renderDevices(i[`area${I.G_}`].devices):void 0))}if(c){var m=i[`service${I.G_}`].open;u.push(e._renderItem(e.localize("ui.panel.config.automation.editor.services"),`service${I.G_}`,!0,!1,!m,m,void 0,i[`service${I.G_}`].open?e._renderDevices(i[`service${I.G_}`].devices):void 0))}return(0,_.qy)(K||(K=ue`<ha-section-title
          >${0}</ha-section-title
        >${0} `),e.localize("ui.panel.config.automation.editor.unassigned"),t?(0,_.qy)(N||(N=ue`<ha-md-list>${0}</ha-md-list>`),u):(0,_.qy)(U||(U=ue`<wa-tree @wa-selection-change=${0}>
              ${0}
            </wa-tree>`),e._handleSelectionChange,u))})),e._renderFloorIcon=e=>t=>e.id&&e.floor?(0,_.qy)(R||(R=ue`<ha-floor-icon
          slot=${0}
          .floor=${0}
        ></ha-floor-icon>`),(0,m.J)(t),e.floor):(0,_.qy)(J||(J=ue`<ha-svg-icon
        slot=${0}
        .path=${0}
      ></ha-svg-icon>`),(0,m.J)(t),ve),e._renderAreaIcon=e=>t=>e?(0,_.qy)(Q||(Q=ue`<ha-icon slot=${0} .icon=${0}></ha-icon>`),(0,m.J)(t),e):(0,_.qy)(X||(X=ue`<ha-svg-icon
            slot=${0}
            .path=${0}
          ></ha-svg-icon>`),(0,m.J)(t),ve),e._renderDomainIcon=t=>i=>{var a;return(0,_.qy)(Y||(Y=ue`
      <img
        slot=${0}
        alt=""
        crossorigin="anonymous"
        referrerpolicy="no-referrer"
        src=${0}
      />
    `),(0,m.J)(i),(0,O.MR)({domain:t,type:"icon",darkOptimized:null===(a=e.hass.themes)||void 0===a?void 0:a.darkMode}))},e._renderEntityIcon=t=>i=>(0,_.qy)(ee||(ee=ue`<state-badge
        slot=${0}
        .stateObj=${0}
        .hass=${0}
      ></state-badge>`),(0,m.J)(i),t,e.hass),e._getAreaDeviceLookupMemoized=(0,f.A)((e=>(0,H.QI)(Object.values(e)))),e._getAreaEntityLookupMemoized=(0,f.A)((e=>(0,H.bQ)(Object.values(e)))),e._getDeviceEntityLookupMemoized=(0,f.A)((e=>(0,M.I3)(Object.values(e)))),e._getSelectedTargetId=(0,f.A)((e=>e&&Object.keys(e).length?`${Object.keys(e)[0].replace("_id","")}${I.G_}${Object.values(e)[0]}`:void 0)),e._getLabelsMemoized=(0,f.A)(S.IV),e._formatId=(0,f.A)((e=>[e.type,e.id].join(I.G_))),e}return(0,c.A)(t,e),(0,n.A)(t,[{key:"willUpdate",value:function(e){(0,h.A)(t,"willUpdate",this,3)([e]),this.hasUpdated||this._initialDataLoad(),(e.has("value")||e.has("narrow"))&&(this._fullHeight=!this.narrow||!this.value||!Object.values(this.value)[0],this.style.setProperty("--max-height",this._fullHeight?"none":"50%"))}},{key:"updated",value:function(e){(e.has("value")||e.has("narrow")||void 0===this._showShowMoreButton)&&this._setShowTargetShowMoreButton()}},{key:"_initialDataLoad",value:(v=(0,s.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this._loadConfigEntries();case 1:this._getTreeData();case 2:return e.a(2)}}),e,this)}))),function(){return v.apply(this,arguments)})},{key:"_setShowTargetShowMoreButton",value:(u=(0,s.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:this._showShowMoreButton=this.narrow&&this.value&&!!Object.values(this.value)[0]&&this.scrollHeight>this.clientHeight;case 2:return e.a(2)}}),e,this)}))),function(){return u.apply(this,arguments)})},{key:"render",value:function(){return this.manifests&&this._configEntryLookup?(0,_.qy)(te||(te=ue`
      ${0}
      ${0}
    `),this.narrow&&this.value?this._renderNarrow(this._entries,this.value):(0,_.qy)(ie||(ie=ue`
            ${0}
            ${0}
            ${0}
          `),this._renderFloors(this.narrow,this._entries,this.value),this._renderUnassigned(this.narrow,this._entries,this.value),this._renderLabels(this.narrow,this.value)),this.narrow&&this._showShowMoreButton&&!this._fullHeight?(0,_.qy)(ae||(ae=ue`
            <div class="targets-show-more">
              <ha-button appearance="filled" @click=${0}>
                ${0}
              </ha-button>
            </div>
          `),this._expandHeight,this.localize("ui.panel.config.automation.editor.show_more")):_.s6):_.s6}},{key:"_renderAreas",value:function(e){var t=Object.keys(e).filter((e=>{var t=e.split(I.G_,2),i=(0,r.A)(t,2)[1];return this.areas[i]})).map((e=>{var t=e.split(I.G_,2),i=(0,r.A)(t,2)[1],a=this.areas[i];return[e,(0,b.A)(a)||a.area_id,a.floor_id||void 0,a.icon]})).map((e=>{var t=(0,r.A)(e,4),i=t[0],a=t[1],s=t[2],o=t[3],n=this._entries[`floor${I.G_}${s||""}`].areas[i],l=n.open,c=n.devices,h=n.entities,d=Object.keys(c).length,u=d+h.length;return this._renderItem(a,i,!1,this._getSelectedTargetId(this.value)===i,!l&&!!u,l,this._renderAreaIcon(o),l?(0,_.qy)(se||(se=ue`
                ${0}
                ${0}
              `),d?this._renderDevices(c):_.s6,h.length?this._renderEntities(h):_.s6):void 0)}));return this.narrow?(0,_.qy)(re||(re=ue`<ha-section-title
          >${0}</ha-section-title
        >
        <ha-md-list>${0}</ha-md-list>`),this.localize("ui.components.target-picker.type.areas"),t):t}},{key:"_renderDevices",value:function(e){var t=Object.keys(e).filter((e=>this.devices[e])).map((e=>{var t,i=this.devices[e],a=i.primary_config_entry?null===(t=this._configEntryLookup)||void 0===t?void 0:t[i.primary_config_entry]:void 0,s=null==a?void 0:a.domain;return[e,(0,$.xn)(i)||e,s]})).sort(((e,t)=>{var i=(0,r.A)(e,2)[1],a=void 0===i?"zzz":i,s=(0,r.A)(t,2)[1],o=void 0===s?"zzz":s;return(0,C.xL)(a,o,this.hass.locale.language)})).map((t=>{var i=(0,r.A)(t,3),a=i[0],s=i[1],o=i[2],n=e[a],l=n.open,c=n.entities;return this._renderItem(s||a,`device${I.G_}${a}`,!1,this._getSelectedTargetId(this.value)===`device${I.G_}${a}`,!l&&!!c.length,l,o?this._renderDomainIcon(o):void 0,l?this._renderEntities(c):void 0)}));return this.narrow?(0,_.qy)(oe||(oe=ue`<ha-section-title
          >${0}</ha-section-title
        >
        <ha-md-list>${0}</ha-md-list>`),this.localize("ui.components.target-picker.type.devices"),t):t}},{key:"_renderDomains",value:function(e,t){var i=Object.keys(e).map((e=>{var i=e.substring(t.length,e.length-I.G_.length);return[e,(0,x.p$)(this.localize,i,this.manifests[i]),i]})).sort(((e,t)=>{var i=(0,r.A)(e,2)[1],a=void 0===i?"zzz":i,s=(0,r.A)(t,2)[1],o=void 0===s?"zzz":s;return(0,C.xL)(a,o,this.hass.locale.language)})).map((t=>{var i=(0,r.A)(t,3),a=i[0],s=i[1],o=i[2],n=e[a],l=n.open,c=n.entities;return this._renderItem(s,a,!0,!1,!l&&!!c.length,l,this._renderDomainIcon(o),l?this._renderEntities(c):void 0)}));return this.narrow?(0,_.qy)(ne||(ne=ue`<ha-section-title
          >${0}</ha-section-title
        >
        <ha-md-list> ${0} </ha-md-list>`),this.localize("ui.components.target-picker.type.devices"),i):i}},{key:"_renderEntities",value:function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:[];if(!e.length)return _.s6;var t=e.filter((e=>this.states[e])).map((e=>{var t,i=this.states[e],a=(0,A.Cf)(i,[{type:"entity"},{type:"device"},{type:"area"}],this.entities,this.devices,this.areas,this.floors),s=(0,r.A)(a,2),o=s[0],n=s[1],l=o||n||e;return null!==(t=this.entities[e])&&void 0!==t&&t.hidden&&(l+=` (${this.localize("ui.panel.config.automation.editor.entity_hidden")})`),[e,l,i]})).sort(((e,t)=>{var i=(0,r.A)(e,2)[1],a=(0,r.A)(t,2)[1];return(0,C.xL)(i,a,this.hass.locale.language)})).map((e=>{var t=(0,r.A)(e,3),i=t[0],a=t[1],s=t[2];return this._renderItem(a,`entity${I.G_}${i}`,!1,this._getSelectedTargetId(this.value)===`entity${I.G_}${i}`,!1,!1,this._renderEntityIcon(s))}));return this.narrow?(0,_.qy)(le||(le=ue`<ha-section-title
          >${0}</ha-section-title
        >
        <ha-md-list>${0}</ha-md-list>`),this.localize("ui.components.target-picker.type.entities"),t):t}},{key:"_renderItem",value:function(e,t){var i=arguments.length>2&&void 0!==arguments[2]&&arguments[2],a=arguments.length>3&&void 0!==arguments[3]&&arguments[3],s=arguments.length>4&&void 0!==arguments[4]&&arguments[4],r=arguments.length>5&&void 0!==arguments[5]&&arguments[5],o=arguments.length>6?arguments[6]:void 0,n=arguments.length>7?arguments[7]:void 0;return this.narrow?(0,_.qy)(ce||(ce=ue`<ha-md-list-item
        interactive
        type="button"
        .target=${0}
        @click=${0}
        .title=${0}
      >
        ${0}
        <div slot="headline">${0}</div>
        <ha-icon-next slot="end"></ha-icon-next>
      </ha-md-list-item>`),t,this._selectItem,e,null==o?void 0:o("start"),e):(0,_.qy)(he||(he=ue`
      <wa-tree-item
        .preventSelection=${0}
        .target=${0}
        .selected=${0}
        .lazy=${0}
        @wa-lazy-load=${0}
        @wa-collapse=${0}
        .expanded=${0}
        .title=${0}
      >
        ${0} ${0} ${0}
      </wa-tree-item>
    `),i,t,a,s,this._expandItem,this._collapseItem,r,e,null==o?void 0:o(),e,n||_.s6)}},{key:"_getTreeData",value:function(){this._floorAreas=(0,V.g)(this.states,this.floors,this.areas,this.devices,this.entities,this._formatId,void 0,void 0,void 0,void 0,void 0,void 0,void 0),this._floorAreas.forEach((e=>{this._entries[e.id||`floor${I.G_}`]={open:!1,areas:{}},e.areas.forEach((t=>{this._entries[e.id||`floor${I.G_}`].areas[t.id]=this._loadArea(t)}))})),this._loadUnassignedDevices(),this._loadUnassignedEntities(),this._entries=Object.assign({},this._entries),this.value&&this._valueChanged(this._getSelectedTargetId(this.value),!this.narrow)}},{key:"_loadUnassignedDevices",value:function(){var e=Object.values(this.devices).filter((e=>!e.area_id)),t={},i={};e.forEach((e=>{var a,s=e.id,r=e.entry_type,o=this.devices[s];if(o&&!o.disabled_by){var n={open:!1,entities:(null===(a=this._getDeviceEntityLookupMemoized(this.entities)[s])||void 0===a?void 0:a.map((e=>e.entity_id)))||[]};"service"!==r?t[s]=n:i[s]=n}})),Object.keys(t).length&&(this._entries=Object.assign(Object.assign({},this._entries),{},{[`area${I.G_}`]:{open:!1,devices:t}})),Object.keys(i).length&&(this._entries=Object.assign(Object.assign({},this._entries),{},{[`service${I.G_}`]:{open:!1,devices:i}}))}},{key:"_loadUnassignedEntities",value:function(){Object.values(this.entities).filter((e=>!e.area_id&&!e.device_id)).forEach((e=>{var t=e.entity_id,i=t.split(".",2)[0],a=this.manifests?this.manifests[i]:void 0;if("helper"===(null==a?void 0:a.integration_type))return this._entries[`helper${I.G_}`]||(this._entries[`helper${I.G_}`]={open:!1,devices:{}}),this._entries[`helper${I.G_}`].devices[`helper_${i}${I.G_}`]||(this._entries[`helper${I.G_}`].devices[`helper_${i}${I.G_}`]={open:!1,entities:[]}),void this._entries[`helper${I.G_}`].devices[`helper_${i}${I.G_}`].entities.push(t);this._entries[`device${I.G_}`]||(this._entries[`device${I.G_}`]={open:!1,devices:{}}),this._entries[`device${I.G_}`].devices[`entity_${i}${I.G_}`]||(this._entries[`device${I.G_}`].devices[`entity_${i}${I.G_}`]={open:!1,entities:[]}),this._entries[`device${I.G_}`].devices[`entity_${i}${I.G_}`].entities.push(t)}))}},{key:"_loadArea",value:function(e){var t=e.id.split(I.G_,2),i=(0,r.A)(t,2)[1],a=this._getAreaDeviceLookupMemoized(this.devices)[i]||[],s=this._getAreaEntityLookupMemoized(this.entities)[i]||[],o={};a.forEach((e=>{var t,i=e.id,a=this.devices[i];a&&!a.disabled_by&&(o[i]={open:!1,entities:(null===(t=this._getDeviceEntityLookupMemoized(this.entities)[i])||void 0===t?void 0:t.map((e=>e.entity_id)))||[]})}));var n=[];return s.forEach((e=>{e.device_id&&o[e.device_id]||n.push(e.entity_id)})),{open:!1,devices:o,entities:n}}},{key:"_expandTreeToItem",value:function(e,t){if("floor"!==e&&"label"!==e)if("entity"!==e)if("device"!==e){if("area"===e){var i,a=`floor${I.G_}${(null===(i=this.areas[t])||void 0===i?void 0:i.floor_id)||""}`;this._entries=Object.assign(Object.assign({},this._entries),{},{[a]:Object.assign(Object.assign({},this._entries[a]),{},{open:!0})})}}else{var s,r,o=null===(s=this.devices[t])||void 0===s?void 0:s.area_id;if(!o){var n=`${"service"===this.devices[t].entry_type?"service":"area"}${I.G_}`;return void(this._entries=Object.assign(Object.assign({},this._entries),{},{[n]:Object.assign(Object.assign({},this._entries[n]),{},{open:!0})}))}var l=`floor${I.G_}${(null===(r=this.areas[o])||void 0===r?void 0:r.floor_id)||""}`,c=`area${I.G_}${o}`;this._entries=Object.assign(Object.assign({},this._entries),{},{[l]:Object.assign(Object.assign({},this._entries[l]),{},{open:!0,areas:Object.assign(Object.assign({},this._entries[l].areas),{},{[c]:Object.assign(Object.assign({},this._entries[l].areas[c]),{},{open:!0})})})})}else{var h,d,u=null===(h=this.entities[t])||void 0===h?void 0:h.device_id,v=u?this.devices[u]:void 0,p=u&&(null==v?void 0:v.area_id)||void 0;if(!p){var _,g,m,f=this.entities[t];if(!u&&f.area_id)_=`floor${I.G_}${(null===(m=this.areas[f.area_id])||void 0===m?void 0:m.floor_id)||""}`,g=`area${I.G_}${f.area_id}`;else if(u)_=`${"service"===v.entry_type?"service":"area"}${I.G_}`,g=u;else{var y,b=t.split(".",1)[0],$="helper"===(null===(y=this.manifests[b])||void 0===y?void 0:y.integration_type);_=$?`helper${I.G_}`:`device${I.G_}`,g=`${$?"helper_":"entity_"}${b}${I.G_}`}return void(this._entries=Object.assign(Object.assign({},this._entries),{},{[_]:Object.assign(Object.assign({},this._entries[_]),{},{open:!0,devices:Object.assign(Object.assign({},this._entries[_].devices),{},{[g]:Object.assign(Object.assign({},this._entries[_].devices[g]),{},{open:!0})})})}))}var A=`floor${I.G_}${(null===(d=this.areas[p])||void 0===d?void 0:d.floor_id)||""}`,C=`area${I.G_}${p}`;this._entries=Object.assign(Object.assign({},this._entries),{},{[A]:Object.assign(Object.assign({},this._entries[A]),{},{open:!0,areas:Object.assign(Object.assign({},this._entries[A].areas),{},{[C]:Object.assign(Object.assign({},this._entries[A].areas[C]),{},{open:!0,devices:Object.assign(Object.assign({},this._entries[A].areas[C].devices),{},{[u]:Object.assign(Object.assign({},this._entries[A].areas[C].devices[u]),{},{open:!0})})})})})})}}},{key:"_handleSelectionChange",value:function(e){var t=e.detail.selection[0];null!=t&&t.target&&this._valueChanged(t.target)}},{key:"_selectItem",value:function(e){var t=e.currentTarget.target;t&&this._valueChanged(t)}},{key:"_valueChanged",value:(d=(0,s.A)((0,a.A)().m((function e(t){var i,s,o,n,l,c,h,d=arguments;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(i=d.length>1&&void 0!==d[1]&&d[1],s=t.split(I.G_,2),o=(0,r.A)(s,2),n=o[0],l=o[1],(0,y.r)(this,"value-changed",{value:{[`${n}_id`]:l||void 0}}),!i||!l){e.n=2;break}return this._expandTreeToItem(n,l),e.n=1,this.updateComplete;case 1:"label"===n?null===(c=this.shadowRoot.querySelector("ha-md-list-item.selected"))||void 0===c||c.scrollIntoView({block:"center"}):null===(h=this.shadowRoot.querySelector("wa-tree-item[selected]"))||void 0===h||h.scrollIntoView({block:"center"});case 2:return e.a(2)}}),e,this)}))),function(e){return d.apply(this,arguments)})},{key:"_toggleItem",value:function(e,t){var i=e.split(I.G_,2),a=(0,r.A)(i,2),s=a[0],o=a[1];if("floor"!==s)if("area"===s&&o){var n,l=`floor${I.G_}${(null===(n=this.areas[o])||void 0===n?void 0:n.floor_id)||""}`;this._entries=Object.assign(Object.assign({},this._entries),{},{[l]:Object.assign(Object.assign({},this._entries[l]),{},{areas:Object.assign(Object.assign({},this._entries[l].areas),{},{[e]:Object.assign(Object.assign({},this._entries[l].areas[e]),{},{open:t})})})})}else if("area"!==s)if("service"!==s)if("device"===s&&o){var c,h,d=null===(c=this.devices[o])||void 0===c?void 0:c.area_id;if(d){var u,v,p,_=`area${I.G_}${null!==(u=null===(v=this.devices[o])||void 0===v?void 0:v.area_id)&&void 0!==u?u:""}`,g=`floor${I.G_}${d&&(null===(p=this.areas[d])||void 0===p?void 0:p.floor_id)||""}`;return void(this._entries=Object.assign(Object.assign({},this._entries),{},{[g]:Object.assign(Object.assign({},this._entries[g]),{},{areas:Object.assign(Object.assign({},this._entries[g].areas),{},{[_]:Object.assign(Object.assign({},this._entries[g].areas[_]),{},{devices:Object.assign(Object.assign({},this._entries[g].areas[_].devices),{},{[o]:Object.assign(Object.assign({},this._entries[g].areas[_].devices[o]),{},{open:t})})})})})}))}var m=`${"service"===(null===(h=this.devices[o])||void 0===h?void 0:h.entry_type)?"service":"area"}${I.G_}`;this._entries=Object.assign(Object.assign({},this._entries),{},{[m]:Object.assign(Object.assign({},this._entries[m]),{},{devices:Object.assign(Object.assign({},this._entries[m].devices),{},{[o]:Object.assign(Object.assign({},this._entries[m].devices[o]),{},{open:t})})})})}else"device"!==s?"helper"!==s?s.startsWith("entity_")?this._entries=Object.assign(Object.assign({},this._entries),{},{[`device${I.G_}`]:Object.assign(Object.assign({},this._entries[`device${I.G_}`]),{},{devices:Object.assign(Object.assign({},this._entries[`device${I.G_}`].devices),{},{[e]:Object.assign(Object.assign({},this._entries[`device${I.G_}`].devices[e]),{},{open:t})})})}):s.startsWith("helper_")&&(this._entries=Object.assign(Object.assign({},this._entries),{},{[`helper${I.G_}`]:Object.assign(Object.assign({},this._entries[`helper${I.G_}`]),{},{devices:Object.assign(Object.assign({},this._entries[`helper${I.G_}`].devices),{},{[e]:Object.assign(Object.assign({},this._entries[`helper${I.G_}`].devices[e]),{},{open:t})})})})):this._entries=Object.assign(Object.assign({},this._entries),{},{[e]:Object.assign(Object.assign({},this._entries[e]),{},{open:t})}):this._entries=Object.assign(Object.assign({},this._entries),{},{[e]:Object.assign(Object.assign({},this._entries[e]),{},{open:t})});else this._entries=Object.assign(Object.assign({},this._entries),{},{[e]:Object.assign(Object.assign({},this._entries[e]),{},{open:t})});else this._entries=Object.assign(Object.assign({},this._entries),{},{[e]:Object.assign(Object.assign({},this._entries[e]),{},{open:t})});else this._entries=Object.assign(Object.assign({},this._entries),{},{[e]:Object.assign(Object.assign({},this._entries[e]),{},{open:t})})}},{key:"_expandItem",value:function(e){var t=e.target.target;this._toggleItem(t,!0)}},{key:"_collapseItem",value:function(e){var t=e.target.target;this._toggleItem(t,!1)}},{key:"_loadConfigEntries",value:(i=(0,s.A)((0,a.A)().m((function e(){var t;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,w.VN)(this.hass);case 1:t=e.v,this._configEntryLookup=Object.fromEntries(t.map((e=>[e.entry_id,e])));case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_expandHeight",value:function(){this._fullHeight=!0,this.style.setProperty("--max-height","none")}}]);var i,d,u,v}(_.WF);pe.styles=(0,_.AH)(de||(de=ue`
    :host {
      --wa-color-neutral-fill-quiet: var(--ha-color-fill-primary-normal-active);
      position: relative;
    }

    ha-section-title {
      top: 0;
      position: sticky;
      z-index: 1;
    }

    wa-tree-item::part(item) {
      height: var(--ha-space-10);
      padding: var(--ha-space-1) var(--ha-space-3);
      cursor: pointer;
      border-inline-start: 0;
    }
    wa-tree-item::part(label) {
      gap: var(--ha-space-3);
      font-family: var(--ha-font-family-heading);
      font-weight: var(--ha-font-weight-medium);
      overflow: hidden;
    }
    ha-md-list-item {
      --md-list-item-label-text-weight: var(--ha-font-weight-medium);
      --md-list-item-label-text-font: var(--ha-font-family-heading);
    }

    .item-label {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    ha-svg-icon,
    ha-icon,
    ha-floor-icon {
      padding: var(--ha-space-1);
      color: var(--ha-color-on-neutral-quiet);
    }

    wa-tree-item::part(item):hover {
      background-color: var(--ha-color-fill-neutral-quiet-hover);
    }

    img {
      width: 24px;
      height: 24px;
      padding: var(--ha-space-1);
    }

    img.domain-icon {
      filter: grayscale(100%);
    }

    state-badge {
      width: 24px;
      height: 24px;
    }

    wa-tree-item[selected],
    wa-tree-item[selected] > ha-svg-icon,
    wa-tree-item[selected] > ha-icon,
    wa-tree-item[selected] > ha-floor-icon {
      color: var(--ha-color-on-primary-normal);
    }

    wa-tree-item[selected]::part(item):hover {
      background-color: var(--ha-color-fill-primary-normal-hover);
    }

    wa-tree-item::part(base).tree-item-selected .item {
      background-color: yellow;
    }

    ha-md-list {
      padding: 0;
      --md-list-item-leading-space: var(--ha-space-3);
      --md-list-item-trailing-space: var(--md-list-item-leading-space);
      --md-list-item-bottom-space: var(--ha-space-1);
      --md-list-item-top-space: var(--md-list-item-bottom-space);
      --md-list-item-supporting-text-font: var(--ha-font-size-s);
      --md-list-item-one-line-container-height: var(--ha-space-10);
    }

    ha-md-list-item.selected {
      background-color: var(--ha-color-fill-primary-normal-active);
      --md-list-item-label-text-color: var(--ha-color-on-primary-normal);
      --icon-primary-color: var(--ha-color-on-primary-normal);
    }

    ha-md-list-item.selected ha-icon,
    ha-md-list-item.selected ha-svg-icon {
      color: var(--ha-color-on-primary-normal);
    }

    .targets-show-more {
      display: flex;
      justify-content: center;
      position: absolute;
      bottom: 0;
      width: 100%;
      padding-bottom: var(--ha-space-2);
      box-shadow: inset var(--ha-shadow-offset-x-lg)
        calc(var(--ha-shadow-offset-y-lg) * -1) var(--ha-shadow-blur-lg)
        var(--ha-shadow-spread-lg) var(--ha-color-shadow-light);
    }

    @media (prefers-color-scheme: dark) {
      .targets-show-more {
        box-shadow: inset var(--ha-shadow-offset-x-lg)
          calc(var(--ha-shadow-offset-y-lg) * -1) var(--ha-shadow-blur-lg)
          var(--ha-shadow-spread-lg) var(--ha-color-shadow-dark);
      }
    }

    @media all and (max-width: 870px), all and (max-height: 500px) {
      :host {
        max-height: var(--max-height, 50%);
        overflow: hidden;
      }
    }
  `)),(0,d.__decorate)([(0,g.MZ)({attribute:!1})],pe.prototype,"hass",void 0),(0,d.__decorate)([(0,g.MZ)({attribute:!1})],pe.prototype,"value",void 0),(0,d.__decorate)([(0,g.MZ)({type:Boolean})],pe.prototype,"narrow",void 0),(0,d.__decorate)([(0,g.MZ)({attribute:!1})],pe.prototype,"manifests",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.$F,subscribe:!0})],pe.prototype,"localize",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.iN,subscribe:!0})],pe.prototype,"states",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.rf,subscribe:!0})],pe.prototype,"floors",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.wn,subscribe:!0})],pe.prototype,"areas",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.xJ,subscribe:!0})],pe.prototype,"devices",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.X1,subscribe:!0})],pe.prototype,"entities",void 0),(0,d.__decorate)([(0,g.wk)(),(0,p.Fg)({context:L.HD,subscribe:!0})],pe.prototype,"_labelRegistry",void 0),(0,d.__decorate)([(0,g.wk)()],pe.prototype,"_floorAreas",void 0),(0,d.__decorate)([(0,g.wk)()],pe.prototype,"_entries",void 0),(0,d.__decorate)([(0,g.wk)()],pe.prototype,"_showShowMoreButton",void 0),(0,d.__decorate)([(0,g.wk)()],pe.prototype,"_fullHeight",void 0),pe=(0,d.__decorate)([(0,g.EM)("ha-automation-add-from-target")],pe),t()}catch(_e){t(_e)}}))},48086:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),s=i(56038),r=i(69683),o=i(6454),n=(i(52675),i(89463),i(28706),i(62826)),l=i(96196),c=i(77845),h=i(94333),d=i(4937),u=i(22786),v=i(92542),p=i(55124),_=i(91720),g=i(85695),m=(i(26537),i(28608),i(42921),i(23897),i(60961),i(88422)),f=e([_,g,m]);[_,g,m]=f.then?(await f)():f;var y,b,$,A,C,k,V,H,w,L,M,x,S,I,O,j,z,G,T,q=e=>e,E=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,s=new Array(i),o=0;o<i;o++)s[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(s))).configEntryLookup={},e.tooltipDescription=!1,e.scrollable=!1,e._itemsScrolled=!1,e._renderTarget=(0,u.A)((t=>t?(0,l.qy)(y||(y=q`<div class="selected-target">
      ${0}
      <div class="label">${0}</div>
    </div>`),e._getSelectedTargetIcon(t[0],t[1]),t[2]):l.s6)),e}return(0,o.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,l.qy)(b||(b=q`<div
      class=${0}
      @scroll=${0}
    >
      ${0}
    </div>`),(0,h.H)({items:!0,blank:this.error||!this.items||!this.items.length,error:this.error,scrolled:this._itemsScrolled}),this._onItemsScroll,this.items||this.error?this.error?(0,l.qy)($||($=q`${0}
              <div>${0}</div>`),this.error,this._renderTarget(this.target)):this.items&&!this.items.length?(0,l.qy)(A||(A=q`${0}
              ${0}`),this.emptyLabel,this.target?(0,l.qy)(C||(C=q`<div>${0}</div>`),this._renderTarget(this.target)):l.s6):(0,d.u)(this.items,((e,t)=>`item-group-${t}`),(e=>this._renderItemList(e.title,e.items))):this.selectLabel)}},{key:"_renderItemList",value:function(e,t){return t&&t.length?(0,l.qy)(k||(k=q`
      <div class="items-title">${0}</div>
      <ha-md-list>
        ${0}
      </ha-md-list>
    `),e,(0,d.u)(t,(e=>e.key),(e=>(0,l.qy)(V||(V=q`
            <ha-md-list-item
              interactive
              type="button"
              .value=${0}
              @click=${0}
            >
              <div slot="headline" class=${0}>
                ${0}${0}
              </div>

              ${0}
              ${0}
              ${0}
              <ha-svg-icon
                slot="end"
                class="plus"
                .path=${0}
              ></ha-svg-icon>
            </ha-md-list-item>
          `),e.key,this._selected,this.target?"item-headline":"",e.name,this._renderTarget(this.target),!this.tooltipDescription&&e.description?(0,l.qy)(H||(H=q`<div slot="supporting-text">${0}</div>`),e.description):l.s6,e.icon?(0,l.qy)(w||(w=q`<span slot="start">${0}</span>`),e.icon):e.iconPath?(0,l.qy)(L||(L=q`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),e.iconPath):l.s6,this.tooltipDescription&&e.description?(0,l.qy)(M||(M=q`<ha-svg-icon
                      tabindex="0"
                      id=${0}
                      slot="end"
                      .path=${0}
                      @click=${0}
                    ></ha-svg-icon>
                    <ha-tooltip
                      .for=${0}
                      @wa-show=${0}
                      @wa-hide=${0}
                      @wa-after-hide=${0}
                      @wa-after-show=${0}
                      >${0}</ha-tooltip
                    > `),`description-tooltip-${e.key}`,"M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",p.d,`description-tooltip-${e.key}`,p.d,p.d,p.d,p.d,e.description):l.s6,"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z")))):l.s6}},{key:"_getSelectedTargetIcon",value:function(e,t){if(!t)return l.s6;if("floor"===e)return(0,l.qy)(x||(x=q`<ha-floor-icon
        .floor=${0}
      ></ha-floor-icon>`),this.hass.floors[t]);if("area"===e&&this.hass.areas[t]){var i=this.hass.areas[t];return i.icon?(0,l.qy)(S||(S=q`<ha-icon .icon=${0}></ha-icon>`),i.icon):(0,l.qy)(I||(I=q`<ha-svg-icon .path=${0}></ha-svg-icon>`),"M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z")}if("device"===e&&this.hass.devices[t]){var a=this.hass.devices[t],s=a.primary_config_entry?this.configEntryLookup[a.primary_config_entry]:void 0,r=null==s?void 0:s.domain;if(r)return(0,l.qy)(O||(O=q`<ha-domain-icon
          slot="start"
          .hass=${0}
          .domain=${0}
          brand-fallback
        ></ha-domain-icon>`),this.hass,r)}if("entity"===e&&this.hass.states[t]){var o=this.hass.states[t];if(o)return(0,l.qy)(j||(j=q`<state-badge
          .stateObj=${0}
          .hass=${0}
          .stateColor=${0}
        ></state-badge>`),o,this.hass,!1)}if("label"===e){var n=this.getLabel(t);return null!=n&&n.icon?(0,l.qy)(z||(z=q`<ha-icon .icon=${0}></ha-icon>`),n.icon):(0,l.qy)(G||(G=q`<ha-svg-icon .path=${0}></ha-svg-icon>`),"M17.63,5.84C17.27,5.33 16.67,5 16,5H5A2,2 0 0,0 3,7V17A2,2 0 0,0 5,19H16C16.67,19 17.27,18.66 17.63,18.15L22,12L17.63,5.84Z")}return l.s6}},{key:"_selected",value:function(e){var t=e.currentTarget;(0,v.r)(this,"value-changed",{value:t.value})}},{key:"_onItemsScroll",value:function(e){var t,i=null!==(t=e.target.scrollTop)&&void 0!==t?t:0;this._itemsScrolled=i>0}},{key:"scrollTo",value:function(e,t){var i,a;"number"==typeof e?null===(i=this._itemsDiv)||void 0===i||i.scrollTo(e,t):null===(a=this._itemsDiv)||void 0===a||a.scrollTo(e)}}])}(l.WF);E.styles=(0,l.AH)(T||(T=q`
    :host {
      display: flex;
    }
    :host([scrollable]) .items {
      overflow: auto;
    }
    .items {
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .items.blank {
      border-radius: var(--ha-border-radius-xl);
      background-color: var(--ha-color-surface-default);
      align-items: center;
      color: var(--ha-color-text-secondary);
      padding: var(--ha-space-0);
      margin: var(--ha-space-0) var(--ha-space-4)
        max(var(--safe-area-inset-bottom), var(--ha-space-3));
      line-height: var(--ha-line-height-expanded);
      justify-content: center;
    }

    .items.error {
      background-color: var(--ha-color-fill-danger-quiet-resting);
      color: var(--ha-color-on-danger-normal);
    }
    .items ha-md-list {
      --md-list-item-two-line-container-height: var(--ha-space-12);
      --md-list-item-leading-space: var(--ha-space-3);
      --md-list-item-trailing-space: var(--md-list-item-leading-space);
      --md-list-item-bottom-space: var(--ha-space-2);
      --md-list-item-top-space: var(--md-list-item-bottom-space);
      --md-list-item-supporting-text-font: var(--ha-font-family-body);
      --ha-md-list-item-gap: var(--ha-space-3);
      gap: var(--ha-space-2);
      padding: var(--ha-space-0) var(--ha-space-4);
    }
    .items ha-md-list ha-md-list-item {
      border-radius: var(--ha-border-radius-lg);
      border: 1px solid var(--ha-color-border-neutral-quiet);
    }

    .items ha-md-list {
      padding-bottom: max(var(--safe-area-inset-bottom), var(--ha-space-3));
    }

    .items .item-headline {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2);
      min-height: var(--ha-space-9);
      flex-wrap: wrap;
    }

    .items-title {
      position: sticky;
      display: flex;
      align-items: center;
      font-weight: var(--ha-font-weight-medium);
      padding-top: var(--ha-space-2);
      padding-bottom: var(--ha-space-2);
      padding-inline-start: var(--ha-space-8);
      padding-inline-end: var(--ha-space-3);
      top: 0;
      z-index: 1;
      background-color: var(--card-background-color);
    }
    ha-bottom-sheet .items-title {
      padding-top: var(--ha-space-3);
    }
    .scrolled .items-title:first-of-type {
      box-shadow: var(--bar-box-shadow);
      border-bottom: 1px solid var(--ha-color-border-neutral-quiet);
    }

    ha-icon-next {
      width: var(--ha-space-6);
    }

    ha-svg-icon.plus {
      color: var(--primary-color);
    }

    .selected-target {
      display: inline-flex;
      gap: var(--ha-space-1);
      justify-content: center;
      align-items: center;
      border-radius: var(--ha-border-radius-md);
      background: var(--ha-color-fill-neutral-normal-resting);
      padding: 0 var(--ha-space-2) 0 var(--ha-space-1);
      color: var(--ha-color-on-neutral-normal);
      overflow: hidden;
    }
    .selected-target .label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .selected-target ha-icon,
    .selected-target ha-svg-icon,
    .selected-target state-badge,
    .selected-target ha-domain-icon {
      display: flex;
      padding: var(--ha-space-1) 0;
    }

    .selected-target state-badge {
      --mdc-icon-size: 24px;
    }
    .selected-target state-badge,
    .selected-target ha-floor-icon {
      display: flex;
      height: 32px;
      width: 32px;
      align-items: center;
    }
    .selected-target ha-domain-icon {
      filter: grayscale(100%);
    }
  `)),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],E.prototype,"hass",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],E.prototype,"items",void 0),(0,n.__decorate)([(0,c.MZ)()],E.prototype,"error",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:"select-label"})],E.prototype,"selectLabel",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:"empty-label"})],E.prototype,"emptyLabel",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],E.prototype,"target",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],E.prototype,"getLabel",void 0),(0,n.__decorate)([(0,c.MZ)({attribute:!1})],E.prototype,"configEntryLookup",void 0),(0,n.__decorate)([(0,c.MZ)({type:Boolean,attribute:"tooltip-description"})],E.prototype,"tooltipDescription",void 0),(0,n.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0})],E.prototype,"scrollable",void 0),(0,n.__decorate)([(0,c.wk)()],E.prototype,"_itemsScrolled",void 0),(0,n.__decorate)([(0,c.P)(".items")],E.prototype,"_itemsDiv",void 0),(0,n.__decorate)([(0,c.Ls)({passive:!0})],E.prototype,"_onItemsScroll",null),E=(0,n.__decorate)([(0,c.EM)("ha-automation-add-items")],E),t()}catch(D){t(D)}}))},28864:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(78261),s=i(94741),r=i(44734),o=i(56038),n=i(69683),l=i(6454),c=i(25460),h=(i(52675),i(89463),i(28706),i(2008),i(48980),i(74423),i(62062),i(44114),i(54554),i(13609),i(18111),i(22489),i(61701),i(26099),i(62826)),d=i(16527),u=(i(32308),i(78648)),v=i(96196),p=i(77845),_=i(29485),g=i(22786),m=i(57947),f=i(92542),y=i(79599),b=(i(96294),i(72434),i(91720)),$=i(12924),A=(i(94343),i(85695)),C=(i(26537),i(28608),i(12109),i(31009),i(265)),k=i(45494),V=i(10038),H=i(34972),w=i(1491),L=i(22800),M=i(41327),x=i(6098),S=i(69847),I=i(84183),O=e([b,$,A]);[b,$,A]=O.then?(await O)():O;var j,z,G,T,q,E,D,Z,F,B,P,W,K,N,U,R,J,Q,X,Y,ee,te,ie,ae=e=>e,se=["separator","entity","device","area","separator","label"],re=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).configEntryLookup={},e.narrow=!1,e.newTriggersAndConditions=!1,e._searchListScrolled=!1,e._getDevicesMemoized=(0,g.A)(w.oG),e._getLabelsMemoized=(0,g.A)(M.IV),e._getEntitiesMemoized=(0,g.A)(L.wz),e._getAreasAndFloorsMemoized=(0,g.A)(k.b),e._selectedSearchItemIndex=-1,e._renderSearchResultRow=(t,i)=>{var a;if(!t)return v.s6;if("string"==typeof t)return(0,v.qy)(j||(j=ae`<ha-section-title>${0}</ha-section-title>`),t);var s,r=["trigger","condition","action","block"].includes(t.type)?"item":(0,x.OJ)(t),o=!1,n=!1,l=!1;"area"!==r&&"floor"!==r||(n=(0,y.qC)(e.hass),o="area"===r&&!(null===(s=t.area)||void 0===s||!s.floor_id));return"entity"===r&&(l=!!e._showEntityId),(0,v.qy)(z||(z=ae`
      <ha-combo-box-item
        id=${0}
        tabindex="-1"
        .type=${0}
        class=${0}
        style=${0}
        .value=${0}
        @click=${0}
      >
        ${0}
        ${0}
        <span slot="headline">${0}</span>
        ${0}
        ${0}
        ${0}
        ${0}
      </ha-combo-box-item>
    `),`search-list-item-${i}`,"empty"===r?"text":"button","empty"===r?"empty":"","area"===t.type&&o?"--md-list-item-leading-space: var(--ha-space-12);":"",t,e._selectSearchResult,"area"===t.type&&o?(0,v.qy)(G||(G=ae`
              <ha-tree-indicator
                style=${0}
                .end=${0}
                slot="start"
              ></ha-tree-indicator>
            `),(0,_.W)({width:"var(--ha-space-12)",position:"absolute",top:"var(--ha-space-0)",left:n?void 0:"var(--ha-space-1)",right:n?"var(--ha-space-1)":void 0,transform:n?"scaleX(-1)":""}),t.last):v.s6,t.icon?(0,v.qy)(T||(T=ae`<ha-icon slot="start" .icon=${0}></ha-icon>`),t.icon):t.icon_path?(0,v.qy)(q||(q=ae`<ha-svg-icon
                slot="start"
                .path=${0}
              ></ha-svg-icon>`),t.icon_path):"entity"===r&&t.stateObj?(0,v.qy)(E||(E=ae`
                  <state-badge
                    slot="start"
                    .stateObj=${0}
                    .hass=${0}
                  ></state-badge>
                `),t.stateObj,e.hass):"device"===r&&t.domain?(0,v.qy)(D||(D=ae`
                    <ha-domain-icon
                      slot="start"
                      .hass=${0}
                      .domain=${0}
                      brand-fallback
                    ></ha-domain-icon>
                  `),e.hass,t.domain):"floor"===r?(0,v.qy)(Z||(Z=ae`<ha-floor-icon
                      slot="start"
                      .floor=${0}
                    ></ha-floor-icon>`),t.floor):"area"===r?(0,v.qy)(F||(F=ae`<ha-svg-icon
                        slot="start"
                        .path=${0}
                      ></ha-svg-icon>`),t.icon_path||"M20 2H4C2.9 2 2 2.9 2 4V20C2 21.11 2.9 22 4 22H20C21.11 22 22 21.11 22 20V4C22 2.9 21.11 2 20 2M4 6L6 4H10.9L4 10.9V6M4 13.7L13.7 4H18.6L4 18.6V13.7M20 18L18 20H13.1L20 13.1V18M20 10.3L10.3 20H5.4L20 5.4V10.3Z"):v.s6,t.primary,t.secondary?(0,v.qy)(B||(B=ae`<span slot="supporting-text">${0}</span>`),t.secondary):v.s6,t.stateObj&&l?(0,v.qy)(P||(P=ae`
              <span slot="supporting-text" class="code">
                ${0}
              </span>
            `),null===(a=t.stateObj)||void 0===a?void 0:a.entity_id):v.s6,!t.domain_name||"entity"===r&&l?v.s6:(0,v.qy)(W||(W=ae`
              <div slot="trailing-supporting-text" class="domain">
                ${0}
              </div>
            `),t.domain_name),"item"===r?(0,v.qy)(K||(K=ae`<ha-svg-icon
              class="plus"
              slot="end"
              .path=${0}
            ></ha-svg-icon>`),"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"):e.narrow?(0,v.qy)(N||(N=ae`<ha-icon-next slot="end"></ha-icon-next>`)):v.s6)},e._keyFunction=e=>"string"==typeof e?e:e.id,e._createFuseIndex=e=>u.A.createIndex(["search_labels"],e),e._fuseIndexes={area:(0,g.A)((t=>e._createFuseIndex(t))),entity:(0,g.A)((t=>e._createFuseIndex(t))),device:(0,g.A)((t=>e._createFuseIndex(t))),label:(0,g.A)((t=>e._createFuseIndex(t))),item:(0,g.A)((t=>e._createFuseIndex(t))),block:(0,g.A)((t=>e._createFuseIndex(t)))},e._getFilteredItems=(0,g.A)(((t,i,a,r,o,n,l)=>{var c=[];if(!l||"item"===l){var h=e._convertItemsToComboBoxItems(o,t);a&&(h=e._filterGroup("item",h,a,{ignoreLocation:!0,includeScore:!0,minMatchCharLength:Math.min(2,e.filter.length)})),!l&&h.length&&c.push(i(`ui.panel.config.automation.editor.${t}s.name`)),c.push.apply(c,(0,s.A)(h))}if("trigger"!==t&&(!l||"block"===l)){var d="action"===t?C.bM:"condition"===t?V.oW:{},u=e._convertItemsToComboBoxItems(Object.keys(d).map((a=>e.convertToItem(a,{},t,i))),"block");a&&(u=e._filterGroup("block",u,a,{ignoreLocation:!0,includeScore:!0,minMatchCharLength:Math.min(2,e.filter.length)})),!l&&u.length&&c.push(i("ui.panel.config.automation.editor.blocks")),c.push.apply(c,(0,s.A)(u))}if(n){if(!l||"entity"===l){var v=e._getEntitiesMemoized(e.hass,void 0,void 0,void 0,void 0,void 0,void 0,void 0,void 0,`entity${x.G_}`);a&&(v=e._filterGroup("entity",v,a,void 0,(e=>{var t;return(null===(t=e.stateObj)||void 0===t?void 0:t.entity_id)===a}))),!l&&v.length&&c.push(i("ui.components.target-picker.type.entities")),c.push.apply(c,(0,s.A)(v))}if(!l||"device"===l){var p=e._getDevicesMemoized(e.hass,r,void 0,void 0,void 0,void 0,void 0,void 0,void 0,`device${x.G_}`);a&&(p=e._filterGroup("device",p,a)),!l&&p.length&&c.push(i("ui.components.target-picker.type.devices")),c.push.apply(c,(0,s.A)(p))}if(!l||"area"===l){var _=e._getAreasAndFloorsMemoized(e.hass.states,e.hass.floors,e.hass.areas,e.hass.devices,e.hass.entities,(0,g.A)((e=>[e.type,e.id].join(x.G_))),void 0,void 0,void 0,void 0,void 0,void 0,void 0);a&&(_=e._filterGroup("area",_,a)),!l&&_.length&&c.push(i("ui.components.target-picker.type.areas")),c.push.apply(c,(0,s.A)(_.map(((e,t)=>{var i=_[t+1];return!i||"area"===e.type&&"floor"===i.type?Object.assign(Object.assign({},e),{},{last:!0}):e}))))}if(!l||"label"===l){var m=e._getLabelsMemoized(e.hass.states,e.hass.areas,e.hass.devices,e.hass.entities,e._labelRegistry,void 0,void 0,void 0,void 0,void 0,void 0,`label${x.G_}`);a&&(m=e._filterGroup("label",m,a)),!l&&m.length&&c.push(i("ui.components.target-picker.type.labels")),c.push.apply(c,(0,s.A)(m))}}return c})),e._convertItemsToComboBoxItems=(e,t)=>e.map((e=>{var i=e.key,a=e.name,s=e.description;return{id:i,primary:a,secondary:s,iconPath:e.iconPath,renderedIcon:e.icon,type:t,search_labels:[i,a,s]}})),e._focusSearchList=()=>{-1===e._selectedSearchItemIndex&&e._selectNextSearchItem()},e._selectSearchResult=t=>{t.stopPropagation();var i=t.currentTarget.value;i&&e._selectSearchItem(i)},e._selectNextSearchItem=t=>{if(null==t||t.stopPropagation(),null==t||t.preventDefault(),e._virtualizerElement){var i=e._virtualizerElement.items,a=i.length-1;if(-1!==a){var s=a===e._selectedSearchItemIndex?e._selectedSearchItemIndex:e._selectedSearchItemIndex+1;if(i[s]){if("string"==typeof i[s]){if(s===a)return;e._selectedSearchItemIndex=s+1}else e._selectedSearchItemIndex=s;e._scrollToSelectedSearchItem()}}else e._resetSelectedSearchItem()}},e._scrollToSelectedSearchItem=()=>{var t,i;null===(t=e._virtualizerElement)||void 0===t||null===(t=t.querySelector(".selected"))||void 0===t||t.classList.remove("selected"),null===(i=e._virtualizerElement)||void 0===i||i.scrollToIndex(e._selectedSearchItemIndex,"end"),requestAnimationFrame((()=>{var t;null===(t=e._virtualizerElement)||void 0===t||null===(t=t.querySelector(`#search-list-item-${e._selectedSearchItemIndex}`))||void 0===t||t.classList.add("selected")}))},e._selectPreviousSearchItem=t=>{if(t.stopPropagation(),t.preventDefault(),e._virtualizerElement&&e._selectedSearchItemIndex>0){var i=e._selectedSearchItemIndex-1,a=e._virtualizerElement.items;if(!a[i])return;if("string"==typeof a[i]){if(0===i)return;e._selectedSearchItemIndex=i-1}else e._selectedSearchItemIndex=i;e._scrollToSelectedSearchItem()}},e._selectFirstSearchItem=t=>{if(t.stopPropagation(),e._virtualizerElement&&e._virtualizerElement.items.length){"string"==typeof e._virtualizerElement.items[0]?e._selectedSearchItemIndex=1:e._selectedSearchItemIndex=0,e._scrollToSelectedSearchItem()}},e._selectLastSearchItem=t=>{if(t.stopPropagation(),e._virtualizerElement&&e._virtualizerElement.items.length){var i=e._virtualizerElement.items.length-1;"string"==typeof e._virtualizerElement.items[i]?e._selectedSearchItemIndex=i-1:e._selectedSearchItemIndex=i,e._scrollToSelectedSearchItem()}},e._pickSelectedSearchItem=t=>{var i,a;t.stopPropagation();var s=null===(i=e._virtualizerElement)||void 0===i?void 0:i.items.filter((e=>"string"!=typeof e));if(s&&1===s.length){var r=s[0];e._selectSearchItem(r)}else if(-1!==e._selectedSearchItemIndex){t.preventDefault();var o=null===(a=e._virtualizerElement)||void 0===a?void 0:a.items[e._selectedSearchItemIndex];o&&e._selectSearchItem(o)}},e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"_showEntityId",get:function(){var e;return null===(e=this.hass.userData)||void 0===e?void 0:e.showEntityIdPicker}},{key:"willUpdate",value:function(e){if(this.hasUpdated||(0,I.i)(),!this.hasUpdated||e.has("filter")){if(this._removeKeyboardShortcuts)return void(this.filter||(this._removeKeyboardShortcuts(),this._removeKeyboardShortcuts=void 0));this._removeKeyboardShortcuts=(0,m.Tc)(window,{ArrowUp:this._selectPreviousSearchItem,ArrowDown:this._selectNextSearchItem,Home:this._selectFirstSearchItem,End:this._selectLastSearchItem,Enter:this._pickSelectedSearchItem})}}},{key:"disconnectedCallback",value:function(){var e;(0,c.A)(t,"disconnectedCallback",this,3)([]),null===(e=this._removeKeyboardShortcuts)||void 0===e||e.call(this)}},{key:"render",value:function(){var e,t=this._getFilteredItems(this.addElementType,this.hass.localize,this.filter,this.configEntryLookup,this.items,this.newTriggersAndConditions,this._selectedSearchSection);return t.length||(e=this._selectedSearchSection?"item"===this._selectedSearchSection?`ui.panel.config.automation.editor.${this.addElementType}s.empty_search.item`:`ui.panel.config.automation.editor.empty_section_search.${this._selectedSearchSection}`:`ui.panel.config.automation.editor.${this.addElementType}s.empty_search.global`),(0,v.qy)(U||(U=ae`
      ${0}
      ${0}
    `),this._renderSections(),e?(0,v.qy)(R||(R=ae`<div class="empty-search">
            ${0}
          </div>`),this.hass.localize(e,{term:(0,v.qy)(J||(J=ae`<b>‘${0}’</b>`),this.filter)})):(0,v.qy)(Q||(Q=ae`
            <div class="search-results">
              <div class="section-title-wrapper">
                ${0}
              </div>
              <lit-virtualizer
                .keyFunction=${0}
                tabindex="0"
                scroller
                .items=${0}
                .renderItem=${0}
                style="min-height: 36px;"
                class=${0}
                @scroll=${0}
                @focus=${0}
                @visibilityChanged=${0}
              >
              </lit-virtualizer>
            </div>
          `),!this._selectedSearchSection&&this._searchSectionTitle?(0,v.qy)(X||(X=ae`<ha-section-title>
                      ${0}
                    </ha-section-title>`),this._searchSectionTitle):v.s6,this._keyFunction,t,this._renderSearchResultRow,this._searchListScrolled?"scrolled":"",this._onScrollSearchList,this._focusSearchList,this._visibilityChanged))}},{key:"_renderSections",value:function(){if("trigger"===this.addElementType&&!this.newTriggersAndConditions)return v.s6;var e=["item"];return"trigger"!==this.addElementType&&e.push("block"),this.newTriggersAndConditions&&e.push.apply(e,se),(0,v.qy)(Y||(Y=ae`
      <ha-chip-set class="sections">
        ${0}
      </ha-chip-set>
    `),e.map((e=>"separator"===e?(0,v.qy)(ee||(ee=ae`<div class="separator"></div>`)):(0,v.qy)(te||(te=ae`<ha-filter-chip
                @click=${0}
                .section-id=${0}
                .selected=${0}
                .label=${0}
              >
              </ha-filter-chip>`),this._toggleSection,e,this._selectedSearchSection===e,this._getSearchSectionLabel(e)))))}},{key:"_onScrollSearchList",value:function(e){var t,i=null!==(t=e.target.scrollTop)&&void 0!==t?t:0;this._searchListScrolled=i>0}},{key:"_visibilityChanged",value:function(e){if(this._virtualizerElement){var t,i=this._virtualizerElement.items[e.first],a=this._virtualizerElement.items[e.first+1];if(void 0===i||void 0===a||"string"==typeof i||"string"==typeof a||0===e.first||0===e.first&&e.last===this._virtualizerElement.items.length-1)return void(this._searchSectionTitle=void 0);t=i.type&&!["area","floor"].includes(i.type)?i.type:(0,x.OJ)(i),this._searchSectionTitle=this._getSearchSectionLabel(t)}}},{key:"_filterGroup",value:function(e,t,i,s,r){var o=this._fuseIndexes[e](t),n=new S.b(t,s||{shouldSort:!1,minMatchCharLength:Math.min(i.length,2)},o).multiTermsSearch(i),l=t;if(n&&(l=n.map((e=>e.item))),!r)return l;var c=l.findIndex((e=>r(e)));if(-1===c)return l;var h=l.splice(c,1),d=(0,a.A)(h,1)[0];return l.unshift(d),l}},{key:"_toggleSection",value:function(e){e.stopPropagation(),this._searchSectionTitle=void 0;var t=e.target["section-id"];t&&(this._selectedSearchSection===t?this._selectedSearchSection=void 0:this._selectedSearchSection=t,this._virtualizerElement&&this._virtualizerElement.scrollToIndex(0))}},{key:"_getSearchSectionLabel",value:function(e){return"block"===e?this.hass.localize("ui.panel.config.automation.editor.blocks"):"item"===e||["trigger","condition","action"].includes(e)?this.hass.localize(`ui.panel.config.automation.editor.${this.addElementType}s.name`):this.hass.localize("ui.components.target-picker.type."+("entity"===e?"entities":`${e}s`))}},{key:"_resetSelectedSearchItem",value:function(){var e;null===(e=this._virtualizerElement)||void 0===e||null===(e=e.querySelector(".selected"))||void 0===e||e.classList.remove("selected"),this._selectedSearchItemIndex=-1}},{key:"_selectSearchItem",value:function(e){(0,f.r)(this,"search-element-picked",e)}}])}(v.WF);re.styles=(0,v.AH)(ie||(ie=ae`
    :host {
      display: flex;
      flex-direction: column;
    }
    .empty-search {
      display: flex;
      flex-direction: column;
      flex: 1;
      padding: var(--ha-space-3);
      border-radius: var(--ha-border-radius-xl);
      background-color: var(--ha-color-surface-default);
      align-items: center;
      color: var(--ha-color-text-secondary);
      margin: var(--ha-space-3) var(--ha-space-4)
        max(var(--safe-area-inset-bottom), var(--ha-space-3));
      line-height: var(--ha-line-height-expanded);
      padding-top: var(--ha-space-6);
      justify-content: start;
    }

    .sections {
      display: flex;
      flex-wrap: nowrap;
      gap: var(--ha-space-2);
      padding: var(--ha-space-3);
      margin-bottom: calc(var(--ha-space-3) * -1);
      overflow: auto;
      overflow-x: auto;
      overflow-y: hidden;
    }

    .sections ha-filter-chip {
      flex-shrink: 0;
      --md-filter-chip-selected-container-color: var(
        --ha-color-fill-primary-normal-hover
      );
      color: var(--primary-color);
    }

    .sections .separator {
      height: var(--ha-space-8);
      width: 0;
      border: 1px solid var(--ha-color-border-neutral-quiet);
    }

    .search-results {
      border-radius: var(--ha-border-radius-xl);
      border: 1px solid var(--ha-color-border-neutral-quiet);
      margin: var(--ha-space-3);
      overflow: hidden;
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    lit-virtualizer ha-section-title {
      width: 100%;
    }

    lit-virtualizer {
      flex: 1;
    }

    lit-virtualizer:focus-visible {
      outline: none;
    }

    ha-combo-box-item {
      width: 100%;
    }

    ha-combo-box-item.selected {
      background-color: var(--ha-color-fill-neutral-quiet-hover);
    }

    @media (prefers-color-scheme: dark) {
      ha-combo-box-item.selected {
        background-color: var(--ha-color-fill-neutral-normal-hover);
      }
    }

    ha-svg-icon.plus {
      color: var(--primary-color);
    }
  `)),(0,h.__decorate)([(0,p.MZ)({attribute:!1})],re.prototype,"hass",void 0),(0,h.__decorate)([(0,p.MZ)()],re.prototype,"filter",void 0),(0,h.__decorate)([(0,p.MZ)({attribute:!1})],re.prototype,"configEntryLookup",void 0),(0,h.__decorate)([(0,p.MZ)({attribute:!1})],re.prototype,"manifests",void 0),(0,h.__decorate)([(0,p.MZ)({attribute:!1})],re.prototype,"items",void 0),(0,h.__decorate)([(0,p.MZ)({type:Boolean})],re.prototype,"narrow",void 0),(0,h.__decorate)([(0,p.MZ)({type:Boolean,attribute:"new-triggers-and-conditions"})],re.prototype,"newTriggersAndConditions",void 0),(0,h.__decorate)([(0,p.MZ)({attribute:!1})],re.prototype,"convertToItem",void 0),(0,h.__decorate)([(0,p.MZ)({attribute:"add-element-type"})],re.prototype,"addElementType",void 0),(0,h.__decorate)([(0,p.wk)()],re.prototype,"_searchSectionTitle",void 0),(0,h.__decorate)([(0,p.wk)()],re.prototype,"_selectedSearchSection",void 0),(0,h.__decorate)([(0,p.wk)()],re.prototype,"_searchListScrolled",void 0),(0,h.__decorate)([(0,p.wk)(),(0,d.Fg)({context:H.HD,subscribe:!0})],re.prototype,"_labelRegistry",void 0),(0,h.__decorate)([(0,p.P)("lit-virtualizer")],re.prototype,"_virtualizerElement",void 0),(0,h.__decorate)([(0,p.Ls)({passive:!0})],re.prototype,"_onScrollSearchList",null),(0,h.__decorate)([(0,p.Ls)({passive:!0})],re.prototype,"_visibilityChanged",null),re=(0,h.__decorate)([(0,p.EM)("ha-automation-add-search")],re),t()}catch(oe){t(oe)}}))}}]);
//# sourceMappingURL=9341.b503c5ee0f895008.js.map