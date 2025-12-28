(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7394"],{61974:function(e,t,i){var a={"./ha-icon-prev":["48268","2477"],"./ha-icon-button-toolbar":["48939","3736"],"./ha-alert":["17963"],"./ha-icon-button-toggle":["35150","2851"],"./ha-svg-icon.ts":["60961"],"./ha-alert.ts":["17963"],"./ha-icon":["22598"],"./ha-icon-next.ts":["28608"],"./ha-qr-code.ts":["16618","1343","6247"],"./ha-icon-overflow-menu.ts":["53623","2016","7644"],"./ha-icon-button-toggle.ts":["35150","2851"],"./ha-icon-button-group":["39651","7760"],"./ha-svg-icon":["60961"],"./ha-icon-button-prev":["80263","8076"],"./ha-icon-button.ts":["60733"],"./ha-icon-overflow-menu":["53623","2016","7644"],"./ha-icon-button-arrow-next":["56231","5500"],"./ha-icon-button-prev.ts":["80263","8076"],"./ha-icon-picker":["88867","624"],"./ha-icon-button-toolbar.ts":["48939","3736"],"./ha-icon-button-arrow-prev.ts":["371"],"./ha-icon-button-next":["29795","9488"],"./ha-icon-next":["28608"],"./ha-icon-picker.ts":["88867","624"],"./ha-icon-prev.ts":["48268","2477"],"./ha-icon-button-arrow-prev":["371"],"./ha-icon-button-next.ts":["29795","9488"],"./ha-icon.ts":["22598"],"./ha-qr-code":["16618","1343","6247"],"./ha-icon-button":["60733"],"./ha-icon-button-group.ts":["39651","7760"],"./ha-icon-button-arrow-next.ts":["56231","5500"]};function r(e){if(!i.o(a,e))return Promise.resolve().then((function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}));var t=a[e],r=t[0];return Promise.all(t.slice(1).map(i.e)).then((function(){return i(r)}))}r.keys=function(){return Object.keys(a)},r.id=61974,e.exports=r},25115:function(e,t,i){var a={"./flow-preview-generic.ts":["66633","3806","4916","5633","7756","6278","1794"],"./flow-preview-template":["71996","3806","4916","5633","7756","6278","9149"],"./flow-preview-generic_camera":["93143","3806","4916","5633","7756","6278","1628"],"./flow-preview-generic_camera.ts":["93143","3806","4916","5633","7756","6278","1628"],"./flow-preview-generic":["66633","3806","4916","5633","7756","6278","1794"],"./flow-preview-template.ts":["71996","3806","4916","5633","7756","6278","9149"]};function r(e){if(!i.o(a,e))return Promise.resolve().then((function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}));var t=a[e],r=t[0];return Promise.all(t.slice(1).map(i.e)).then((function(){return i(r)}))}r.keys=function(){return Object.keys(a)},r.id=25115,e.exports=r},45817:function(e,t,i){"use strict";i.d(t,{d:function(){return a}});i(50113),i(25276),i(34782),i(18111),i(20116),i(26099);var a=function(e){var t=!(arguments.length>1&&void 0!==arguments[1])||arguments[1];if(!(e.defaultPrevented||0!==e.button||e.metaKey||e.ctrlKey||e.shiftKey)){var i=e.composedPath().find((e=>"A"===e.tagName));if(i&&!i.target&&!i.hasAttribute("download")&&"external"!==i.getAttribute("rel")){var a=i.href;if(a&&-1===a.indexOf("mailto:")){var r=window.location,n=r.origin||r.protocol+"//"+r.host;if(a.startsWith(n)&&"#"!==(a=a.slice(n.length)))return t&&e.preventDefault(),a}}}}},48565:function(e,t,i){"use strict";i.d(t,{d:function(){return a}});var a=e=>{switch(e.language){case"cs":case"de":case"fi":case"fr":case"sk":case"sv":return" ";default:return""}}},86451:function(e,t,i){"use strict";var a,r,n,o,s,l,c=i(44734),d=i(56038),h=i(69683),p=i(6454),u=(i(28706),i(62826)),f=i(96196),v=i(77845),g=e=>e,_=function(e){function t(){var e;(0,c.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,h.A)(this,t,[].concat(a))).subtitlePosition="below",e.showBorder=!1,e}return(0,p.A)(t,e),(0,d.A)(t,[{key:"render",value:function(){var e=(0,f.qy)(a||(a=g`<div class="header-title">
      <slot name="title"></slot>
    </div>`)),t=(0,f.qy)(r||(r=g`<div class="header-subtitle">
      <slot name="subtitle"></slot>
    </div>`));return(0,f.qy)(n||(n=g`
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
    `),"above"===this.subtitlePosition?(0,f.qy)(o||(o=g`${0}${0}`),t,e):(0,f.qy)(s||(s=g`${0}${0}`),e,t))}}],[{key:"styles",get:function(){return[(0,f.AH)(l||(l=g`
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
      `))]}}])}(f.WF);(0,u.__decorate)([(0,v.MZ)({type:String,attribute:"subtitle-position"})],_.prototype,"subtitlePosition",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],_.prototype,"showBorder",void 0),_=(0,u.__decorate)([(0,v.EM)("ha-dialog-header")],_)},23442:function(e,t,i){"use strict";i.d(t,{$:function(){return a}});i(52675),i(89463),i(16280),i(34782),i(18111),i(7588),i(26099),i(23500);var a=e=>{var t={};return e.forEach((e=>{var i,r;if(void 0!==(null===(i=e.description)||void 0===i?void 0:i.suggested_value)&&null!==(null===(r=e.description)||void 0===r?void 0:r.suggested_value))t[e.name]=e.description.suggested_value;else if("default"in e)t[e.name]=e.default;else if("expandable"===e.type){var n=a(e.schema);(e.required||Object.keys(n).length)&&(t[e.name]=n)}else if(e.required){if("boolean"===e.type)t[e.name]=!1;else if("string"===e.type)t[e.name]="";else if("integer"===e.type)t[e.name]="valueMin"in e?e.valueMin:0;else if("constant"===e.type)t[e.name]=e.value;else if("float"===e.type)t[e.name]=0;else if("select"===e.type){if(e.options.length){var o=e.options[0];t[e.name]=Array.isArray(o)?o[0]:o}}else if("positive_time_period_dict"===e.type)t[e.name]={hours:0,minutes:0,seconds:0};else if("selector"in e){var s,l=e.selector;if("device"in l)t[e.name]=null!==(s=l.device)&&void 0!==s&&s.multiple?[]:"";else if("entity"in l){var c;t[e.name]=null!==(c=l.entity)&&void 0!==c&&c.multiple?[]:""}else if("area"in l){var d;t[e.name]=null!==(d=l.area)&&void 0!==d&&d.multiple?[]:""}else if("label"in l){var h;t[e.name]=null!==(h=l.label)&&void 0!==h&&h.multiple?[]:""}else if("boolean"in l)t[e.name]=!1;else if("addon"in l||"attribute"in l||"file"in l||"icon"in l||"template"in l||"text"in l||"theme"in l||"object"in l)t[e.name]="";else if("number"in l){var p,u;t[e.name]=null!==(p=null===(u=l.number)||void 0===u?void 0:u.min)&&void 0!==p?p:0}else if("select"in l){var f;if(null!==(f=l.select)&&void 0!==f&&f.options.length){var v=l.select.options[0],g="string"==typeof v?v:v.value;t[e.name]=l.select.multiple?[g]:g}}else if("country"in l){var _;null!==(_=l.country)&&void 0!==_&&null!==(_=_.countries)&&void 0!==_&&_.length&&(t[e.name]=l.country.countries[0])}else if("language"in l){var m;null!==(m=l.language)&&void 0!==m&&null!==(m=m.languages)&&void 0!==m&&m.length&&(t[e.name]=l.language.languages[0])}else if("duration"in l)t[e.name]={hours:0,minutes:0,seconds:0};else if("time"in l)t[e.name]="00:00:00";else if("date"in l||"datetime"in l){var y=(new Date).toISOString().slice(0,10);t[e.name]=`${y}T00:00:00`}else if("color_rgb"in l)t[e.name]=[0,0,0];else if("color_temp"in l){var w,b;t[e.name]=null!==(w=null===(b=l.color_temp)||void 0===b?void 0:b.min_mireds)&&void 0!==w?w:153}else if("action"in l||"trigger"in l||"condition"in l)t[e.name]=[];else if("media"in l||"target"in l)t[e.name]={};else{if(!("state"in l))throw new Error(`Selector ${Object.keys(l)[0]} not supported in initial form data`);var k;t[e.name]=null!==(k=l.state)&&void 0!==k&&k.multiple?[]:""}}}else;})),t}},91120:function(e,t,i){"use strict";var a,r,n,o,s,l,c,d,h,p=i(78261),u=i(61397),f=i(31432),v=i(50264),g=i(44734),_=i(56038),m=i(69683),y=i(6454),w=i(25460),b=(i(28706),i(23792),i(62062),i(18111),i(7588),i(61701),i(5506),i(26099),i(3362),i(23500),i(62953),i(62826)),k=i(96196),$=i(77845),A=i(51757),x=i(92542),C=(i(17963),i(87156),e=>e),M={boolean:()=>i.e("2018").then(i.bind(i,49337)),constant:()=>i.e("9938").then(i.bind(i,37449)),float:()=>i.e("812").then(i.bind(i,5863)),grid:()=>i.e("798").then(i.bind(i,81213)),expandable:()=>i.e("8550").then(i.bind(i,29989)),integer:()=>i.e("1364").then(i.bind(i,28175)),multi_select:()=>Promise.all([i.e("2016"),i.e("3956"),i.e("3616")]).then(i.bind(i,59827)),positive_time_period_dict:()=>i.e("5846").then(i.bind(i,19797)),select:()=>i.e("6262").then(i.bind(i,29317)),string:()=>i.e("8389").then(i.bind(i,33092)),optional_actions:()=>i.e("1454").then(i.bind(i,2173))},z=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null,E=function(e){function t(){var e;(0,g.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,m.A)(this,t,[].concat(a))).narrow=!1,e.disabled=!1,e}return(0,y.A)(t,e),(0,_.A)(t,[{key:"getFormProperties",value:function(){return{}}},{key:"focus",value:(i=(0,v.A)((0,u.A)().m((function e(){var t,i,a,r,n;return(0,u.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.n=1,this.updateComplete;case 1:if(t=this.renderRoot.querySelector(".root")){e.n=2;break}return e.a(2);case 2:i=(0,f.A)(t.children),e.p=3,i.s();case 4:if((a=i.n()).done){e.n=7;break}if("HA-ALERT"===(r=a.value).tagName){e.n=6;break}if(!(r instanceof k.mN)){e.n=5;break}return e.n=5,r.updateComplete;case 5:return r.focus(),e.a(3,7);case 6:e.n=4;break;case 7:e.n=9;break;case 8:e.p=8,n=e.v,i.e(n);case 9:return e.p=9,i.f(),e.f(9);case 10:return e.a(2)}}),e,this,[[3,8,9,10]])}))),function(){return i.apply(this,arguments)})},{key:"willUpdate",value:function(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{var t;"selector"in e||null===(t=M[e.type])||void 0===t||t.call(M)}))}},{key:"render",value:function(){return(0,k.qy)(a||(a=C`
      <div class="root" part="root">
        ${0}
        ${0}
      </div>
    `),this.error&&this.error.base?(0,k.qy)(r||(r=C`
              <ha-alert alert-type="error">
                ${0}
              </ha-alert>
            `),this._computeError(this.error.base,this.schema)):"",this.schema.map((e=>{var t,i=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),a=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return(0,k.qy)(n||(n=C`
            ${0}
            ${0}
          `),i?(0,k.qy)(o||(o=C`
                  <ha-alert own-margin alert-type="error">
                    ${0}
                  </ha-alert>
                `),this._computeError(i,e)):a?(0,k.qy)(s||(s=C`
                    <ha-alert own-margin alert-type="warning">
                      ${0}
                    </ha-alert>
                  `),this._computeWarning(a,e)):"","selector"in e?(0,k.qy)(l||(l=C`<ha-selector
                  .schema=${0}
                  .hass=${0}
                  .narrow=${0}
                  .name=${0}
                  .selector=${0}
                  .value=${0}
                  .label=${0}
                  .disabled=${0}
                  .placeholder=${0}
                  .helper=${0}
                  .localizeValue=${0}
                  .required=${0}
                  .context=${0}
                ></ha-selector>`),e,this.hass,this.narrow,e.name,e.selector,z(this.data,e),this._computeLabel(e,this.data),e.disabled||this.disabled||!1,e.required?void 0:e.default,this._computeHelper(e),this.localizeValue,e.required||!1,this._generateContext(e)):(0,A._)(this.fieldElementName(e.type),Object.assign({schema:e,data:z(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:null===(t=this.hass)||void 0===t?void 0:t.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e)},this.getFormProperties())))})))}},{key:"fieldElementName",value:function(e){return`ha-form-${e}`}},{key:"_generateContext",value:function(e){if(e.context){for(var t={},i=0,a=Object.entries(e.context);i<a.length;i++){var r=(0,p.A)(a[i],2),n=r[0],o=r[1];t[n]=this.data[o]}return t}}},{key:"createRenderRoot",value:function(){var e=(0,w.A)(t,"createRenderRoot",this,3)([]);return this.addValueChangedListener(e),e}},{key:"addValueChangedListener",value:function(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();var t=e.target.schema;if(e.target!==this){var i=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data=Object.assign(Object.assign({},this.data),i),(0,x.r)(this,"value-changed",{value:this.data})}}))}},{key:"_computeLabel",value:function(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}},{key:"_computeHelper",value:function(e){return this.computeHelper?this.computeHelper(e):""}},{key:"_computeError",value:function(e,t){return Array.isArray(e)?(0,k.qy)(c||(c=C`<ul>
        ${0}
      </ul>`),e.map((e=>(0,k.qy)(d||(d=C`<li>
              ${0}
            </li>`),this.computeError?this.computeError(e,t):e)))):this.computeError?this.computeError(e,t):e}},{key:"_computeWarning",value:function(e,t){return this.computeWarning?this.computeWarning(e,t):e}}]);var i}(k.WF);E.shadowRootOptions={mode:"open",delegatesFocus:!0},E.styles=(0,k.AH)(h||(h=C`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `)),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"hass",void 0),(0,b.__decorate)([(0,$.MZ)({type:Boolean})],E.prototype,"narrow",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"data",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"schema",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"error",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"warning",void 0),(0,b.__decorate)([(0,$.MZ)({type:Boolean})],E.prototype,"disabled",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"computeError",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"computeWarning",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"computeLabel",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"computeHelper",void 0),(0,b.__decorate)([(0,$.MZ)({attribute:!1})],E.prototype,"localizeValue",void 0),E=(0,b.__decorate)([(0,$.EM)("ha-form")],E)},28089:function(e,t,i){"use strict";var a,r,n=i(61397),o=i(50264),s=i(44734),l=i(56038),c=i(69683),d=i(6454),h=i(25460),p=(i(28706),i(62826)),u=i(96196),f=i(77845),v=i(3164),g=i(94741),_=i(75864),m=i(59787),y=(i(2008),i(23418),i(74423),i(23792),i(62062),i(72712),i(34782),i(18111),i(22489),i(61701),i(18237),i(26099),i(3362),i(27495),i(62953),i(1420)),w=i(30015),b=i.n(w),k=i(92542),$=(i(3296),i(27208),i(48408),i(14603),i(47566),i(98721),i(2209)),A=function(){var e=(0,o.A)((0,n.A)().m((function e(t,r,o){return(0,n.A)().w((function(e){for(;;)if(0===e.n)return a||(a=(0,$.LV)(new Worker(new URL(i.p+i.u("5640"),i.b)))),e.a(2,a.renderMarkdown(t,r,o))}),e)})));return function(t,i,a){return e.apply(this,arguments)}}(),x=(i(36033),e=>e),C=e=>(0,u.qy)(r||(r=x`${0}`),e),M=new(function(){return(0,l.A)((function e(t){(0,s.A)(this,e),this._cache=new Map,this._expiration=t}),[{key:"get",value:function(e){return this._cache.get(e)}},{key:"set",value:function(e,t){this._cache.set(e,t),this._expiration&&window.setTimeout((()=>this._cache.delete(e)),this._expiration)}},{key:"has",value:function(e){return this._cache.has(e)}}])}())(1e3),z={reType:(0,m.A)(/((\[!(caution|important|note|tip|warning)\])(?:\s|\\n)?)/i,{input:1,type:3}),typeToHaAlert:{caution:"error",important:"info",note:"info",tip:"success",warning:"warning"}},E=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(a))).allowSvg=!1,e.allowDataUrl=!1,e.breaks=!1,e.lazyImages=!1,e.cache=!1,e._renderPromise=Promise.resolve(),e._resize=()=>(0,k.r)((0,_.A)(e),"content-resize"),e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"disconnectedCallback",value:function(){if((0,h.A)(t,"disconnectedCallback",this,3)([]),this.cache){var e=this._computeCacheKey();M.set(e,this.innerHTML)}}},{key:"createRenderRoot",value:function(){return this}},{key:"update",value:function(e){(0,h.A)(t,"update",this,3)([e]),void 0!==this.content&&(this._renderPromise=this._render())}},{key:"getUpdateComplete",value:(r=(0,o.A)((0,n.A)().m((function e(){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,h.A)(t,"getUpdateComplete",this,3)([]);case 1:return e.n=2,this._renderPromise;case 2:return e.a(2,!0)}}),e,this)}))),function(){return r.apply(this,arguments)})},{key:"willUpdate",value:function(e){if(!this.innerHTML&&this.cache){var t=this._computeCacheKey();M.has(t)&&((0,u.XX)(C((0,y._)(M.get(t))),this.renderRoot),this._resize())}}},{key:"_computeCacheKey",value:function(){return b()({content:this.content,allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl,breaks:this.breaks})}},{key:"_render",value:(a=(0,o.A)((0,n.A)().m((function e(){var t,a,r,o=this;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,A(String(this.content),{breaks:this.breaks,gfm:!0},{allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl});case 1:t=e.v,(0,u.XX)(C((0,y._)(t.join(""))),this.renderRoot),this._resize(),a=document.createTreeWalker(this,NodeFilter.SHOW_ELEMENT,null),r=(0,n.A)().m((function e(){var t,r,s,l,c;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:(t=a.currentNode)instanceof HTMLAnchorElement&&t.host!==document.location.host?(t.target="_blank",t.rel="noreferrer noopener"):t instanceof HTMLImageElement?(o.lazyImages&&(t.loading="lazy"),t.addEventListener("load",o._resize)):t instanceof HTMLQuoteElement?(s=(null===(r=t.firstElementChild)||void 0===r||null===(r=r.firstChild)||void 0===r?void 0:r.textContent)&&z.reType.exec(t.firstElementChild.firstChild.textContent))&&(l=s.groups.type,(c=document.createElement("ha-alert")).alertType=z.typeToHaAlert[l.toLowerCase()],c.append.apply(c,(0,g.A)(Array.from(t.childNodes).map((e=>{var t=Array.from(e.childNodes);if(!o.breaks&&t.length){var i,a=t[0];a.nodeType===Node.TEXT_NODE&&a.textContent===s.input&&null!==(i=a.textContent)&&void 0!==i&&i.includes("\n")&&(a.textContent=a.textContent.split("\n").slice(1).join("\n"))}return t})).reduce(((e,t)=>e.concat(t)),[]).filter((e=>e.textContent&&e.textContent!==s.input)))),a.parentNode().replaceChild(c,t)):t instanceof HTMLElement&&["ha-alert","ha-qr-code","ha-icon","ha-svg-icon"].includes(t.localName)&&i(61974)(`./${t.localName}`);case 1:return e.a(2)}}),e)}));case 2:if(!a.nextNode()){e.n=4;break}return e.d((0,v.A)(r()),3);case 3:e.n=2;break;case 4:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})}]);var a,r}(u.mN);(0,p.__decorate)([(0,f.MZ)()],E.prototype,"content",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:"allow-svg",type:Boolean})],E.prototype,"allowSvg",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:"allow-data-url",type:Boolean})],E.prototype,"allowDataUrl",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean})],E.prototype,"breaks",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean,attribute:"lazy-images"})],E.prototype,"lazyImages",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean})],E.prototype,"cache",void 0),E=(0,p.__decorate)([(0,f.EM)("ha-markdown-element")],E);var D,S,F=e=>e,q=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(a))).allowSvg=!1,e.allowDataUrl=!1,e.breaks=!1,e.lazyImages=!1,e.cache=!1,e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"getUpdateComplete",value:(i=(0,o.A)((0,n.A)().m((function e(){var i,a;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,h.A)(t,"getUpdateComplete",this,3)([]);case 1:return a=e.v,e.n=2,null===(i=this._markdownElement)||void 0===i?void 0:i.updateComplete;case 2:return e.a(2,a)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"render",value:function(){return this.content?(0,u.qy)(D||(D=F`<ha-markdown-element
      .content=${0}
      .allowSvg=${0}
      .allowDataUrl=${0}
      .breaks=${0}
      .lazyImages=${0}
      .cache=${0}
    ></ha-markdown-element>`),this.content,this.allowSvg,this.allowDataUrl,this.breaks,this.lazyImages,this.cache):u.s6}}]);var i}(u.WF);q.styles=(0,u.AH)(S||(S=F`
    :host {
      display: block;
    }
    ha-markdown-element {
      -ms-user-select: text;
      -webkit-user-select: text;
      -moz-user-select: text;
    }
    ha-markdown-element > *:first-child {
      margin-top: 0;
    }
    ha-markdown-element > *:last-child {
      margin-bottom: 0;
    }
    ha-alert {
      display: block;
      margin: var(--ha-space-1) 0;
    }
    a {
      color: var(--markdown-link-color, var(--primary-color));
    }
    img {
      background-color: var(--markdown-image-background-color);
      border-radius: var(--markdown-image-border-radius);
      max-width: 100%;
      height: auto;
      width: auto;
      transition: height 0.2s ease-in-out;
    }
    p:first-child > img:first-child {
      vertical-align: top;
    }
    p:first-child > img:last-child {
      vertical-align: top;
    }
    :host > ul,
    :host > ol {
      padding-inline-start: var(--markdown-list-indent, revert);
    }
    li {
      &:has(input[type="checkbox"]) {
        list-style: none;
        & > input[type="checkbox"] {
          margin-left: 0;
        }
      }
    }
    svg {
      background-color: var(--markdown-svg-background-color, none);
      color: var(--markdown-svg-color, none);
    }
    code,
    pre {
      background-color: var(--markdown-code-background-color, none);
      border-radius: var(--ha-border-radius-sm);
      color: var(--markdown-code-text-color, inherit);
    }
    code {
      font-size: var(--ha-font-size-s);
      padding: 0.2em 0.4em;
    }
    pre code {
      padding: 0;
    }
    pre {
      padding: var(--ha-space-4);
      overflow: auto;
      line-height: var(--ha-line-height-condensed);
      font-family: var(--ha-font-family-code);
    }
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      line-height: initial;
    }
    h2 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-bold);
    }
    hr {
      border-color: var(--divider-color);
      border-bottom: none;
      margin: var(--ha-space-4) 0;
    }
    table {
      border-collapse: var(--markdown-table-border-collapse, collapse);
    }
    div:has(> table) {
      overflow: auto;
    }
    th {
      text-align: start;
    }
    td,
    th {
      border-width: var(--markdown-table-border-width, 1px);
      border-style: var(--markdown-table-border-style, solid);
      border-color: var(--markdown-table-border-color, var(--divider-color));
      padding: 0.25em 0.5em;
    }
    blockquote {
      border-left: 4px solid var(--divider-color);
      margin-inline: 0;
      padding-inline: 1em;
    }
  `)),(0,p.__decorate)([(0,f.MZ)()],q.prototype,"content",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:"allow-svg",type:Boolean})],q.prototype,"allowSvg",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:"allow-data-url",type:Boolean})],q.prototype,"allowDataUrl",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean})],q.prototype,"breaks",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean,attribute:"lazy-images"})],q.prototype,"lazyImages",void 0),(0,p.__decorate)([(0,f.MZ)({type:Boolean})],q.prototype,"cache",void 0),(0,p.__decorate)([(0,f.P)("ha-markdown-element")],q.prototype,"_markdownElement",void 0),q=(0,p.__decorate)([(0,f.EM)("ha-markdown")],q)},64109:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),n=i(69683),o=i(25460),s=i(6454),l=i(62826),c=i(65686),d=i(96196),h=i(77845),p=e([c]);c=(p.then?(await p)():p)[0];var u,f=e=>e,v=function(e){function t(){return(0,a.A)(this,t),(0,n.A)(this,t,arguments)}return(0,s.A)(t,e),(0,r.A)(t,[{key:"updated",value:function(e){if((0,o.A)(t,"updated",this,3)([e]),e.has("size"))switch(this.size){case"tiny":this.style.setProperty("--ha-progress-ring-size","16px");break;case"small":this.style.setProperty("--ha-progress-ring-size","28px");break;case"medium":this.style.setProperty("--ha-progress-ring-size","48px");break;case"large":this.style.setProperty("--ha-progress-ring-size","68px");break;case void 0:this.style.removeProperty("--ha-progress-ring-size")}}}],[{key:"styles",get:function(){return[c.A.styles,(0,d.AH)(u||(u=f`
        :host {
          --indicator-color: var(
            --ha-progress-ring-indicator-color,
            var(--primary-color)
          );
          --track-color: var(
            --ha-progress-ring-divider-color,
            var(--divider-color)
          );
          --track-width: 4px;
          --speed: 3.5s;
          --size: var(--ha-progress-ring-size, 48px);
        }
      `))]}}])}(c.A);(0,l.__decorate)([(0,h.MZ)()],v.prototype,"size",void 0),v=(0,l.__decorate)([(0,h.EM)("ha-progress-ring")],v),t()}catch(g){t(g)}}))},41558:function(e,t,i){"use strict";i.d(t,{KC:function(){return d},Vy:function(){return l},ds:function(){return n},ew:function(){return s},g5:function(){return c},tl:function(){return o}});var a=i(9477),r=i(31136),n=(e,t,i)=>e.connection.subscribeMessage(i,{type:"assist_satellite/intercept_wake_word",entity_id:t}),o=(e,t)=>e.callWS({type:"assist_satellite/test_connection",entity_id:t}),s=(e,t,i)=>e.callService("assist_satellite","announce",i,{entity_id:t}),l=(e,t)=>e.callWS({type:"assist_satellite/get_configuration",entity_id:t}),c=(e,t,i)=>e.callWS({type:"assist_satellite/set_wake_words",entity_id:t,wake_word_ids:i}),d=e=>e&&e.state!==r.Hh&&(0,a.$)(e,1)},54193:function(e,t,i){"use strict";i.d(t,{Hg:function(){return a},e0:function(){return r}});i(61397),i(50264),i(74423),i(62062),i(18111),i(61701),i(33110),i(26099),i(3362);var a=e=>e.map((e=>{if("string"!==e.type)return e;switch(e.name){case"username":return Object.assign(Object.assign({},e),{},{autocomplete:"username",autofocus:!0});case"password":return Object.assign(Object.assign({},e),{},{autocomplete:"current-password"});case"code":return Object.assign(Object.assign({},e),{},{autocomplete:"one-time-code",autofocus:!0});default:return e}})),r=(e,t)=>e.callWS({type:"auth/sign_path",path:t})},23608:function(e,t,i){"use strict";i.d(t,{PN:function(){return n},jm:function(){return o},sR:function(){return s},t1:function(){return r},t2:function(){return c},yu:function(){return l}});var a={"HA-Frontend-Base":`${location.protocol}//${location.host}`},r=(e,t,i)=>{var r;return e.callApi("POST","config/config_entries/flow",{handler:t,show_advanced_options:Boolean(null===(r=e.userData)||void 0===r?void 0:r.showAdvanced),entry_id:i},a)},n=(e,t)=>e.callApi("GET",`config/config_entries/flow/${t}`,void 0,a),o=(e,t,i)=>e.callApi("POST",`config/config_entries/flow/${t}`,i,a),s=(e,t)=>e.callApi("DELETE",`config/config_entries/flow/${t}`),l=(e,t)=>e.callApi("GET","config/config_entries/flow_handlers"+(t?`?type=${t}`:"")),c=e=>e.sendMessagePromise({type:"config_entries/flow/progress"})},86807:function(e,t,i){"use strict";i.d(t,{K:function(){return r},P:function(){return a}});var a=(e,t)=>e.subscribeEvents(t,"data_entry_flow_progressed"),r=(e,t)=>e.subscribeEvents(t,"data_entry_flow_progress_update")},31136:function(e,t,i){"use strict";i.d(t,{HV:function(){return n},Hh:function(){return r},KF:function(){return s},ON:function(){return o},g0:function(){return d},s7:function(){return l}});var a=i(99245),r="unavailable",n="unknown",o="on",s="off",l=[r,n],c=[r,n,s],d=(0,a.g)(l);(0,a.g)(c)},73103:function(e,t,i){"use strict";i.d(t,{F:function(){return n},Q:function(){return r}});i(74423);var a=["generic_camera","template"],r=(e,t,i,a,r,n)=>e.connection.subscribeMessage(n,{type:`${t}/start_preview`,flow_id:i,flow_type:a,user_input:r}),n=e=>a.includes(e)?e:"generic"},90313:function(e,t,i){"use strict";i.a(e,(async function(e,a){try{i.r(t);var r=i(61397),n=i(50264),o=i(44734),s=i(56038),l=i(69683),c=i(6454),d=i(25460),h=(i(28706),i(2008),i(74423),i(23792),i(62062),i(18111),i(22489),i(61701),i(33110),i(26099),i(16034),i(3362),i(62953),i(62826)),p=i(96196),u=i(77845),f=i(22786),v=i(92542),g=(i(95637),i(86451),i(60733),i(86807)),_=i(39396),m=i(62001),y=i(10234),w=i(93056),b=i(64533),k=i(12083),$=i(84398),A=i(19486),x=(i(59395),i(12527)),C=i(35804),M=i(53264),z=i(73042),E=e([w,b,k,$,A,x]);[w,b,k,$,A,x]=E.then?(await E)():E;var D,S,F,q,O,P,T,U,Z,H,L,j,N=e=>e,R=0,B=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(a)))._instance=R,e._devices=(0,f.A)(((e,t,i,a)=>e&&i?t.filter((e=>e.config_entries.includes(i)||(null==a?void 0:a.includes(e.id)))):[])),e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"showDialog",value:(h=(0,n.A)((0,r.A)().m((function e(t){var i,a,n,o,s,l;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(this._params=t,this._instance=R++,i=this._instance,!t.startFlowHandler){e.n=6;break}return this._loading="loading_flow",this._handler=t.startFlowHandler,e.p=1,e.n=2,this._params.flowConfig.createFlow(this.hass,t.startFlowHandler);case 2:a=e.v,e.n=4;break;case 3:return e.p=3,s=e.v,this.closeDialog(),"string"!=typeof(n=s.message||s.body||"Unknown error")&&(n=JSON.stringify(n)),(0,y.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:`${this.hass.localize("ui.panel.config.integrations.config_flow.could_not_load")}: ${n}`}),e.a(2);case 4:if(i===this._instance){e.n=5;break}return e.a(2);case 5:e.n=12;break;case 6:if(!t.continueFlowId){e.n=11;break}return this._loading="loading_flow",e.p=7,e.n=8,t.flowConfig.fetchFlow(this.hass,t.continueFlowId);case 8:a=e.v,e.n=10;break;case 9:return e.p=9,l=e.v,this.closeDialog(),"string"!=typeof(o=l.message||l.body||"Unknown error")&&(o=JSON.stringify(o)),(0,y.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:`${this.hass.localize("ui.panel.config.integrations.config_flow.could_not_load")}: ${o}`}),e.a(2);case 10:e.n=12;break;case 11:return e.a(2);case 12:if(i===this._instance){e.n=13;break}return e.a(2);case 13:this._processStep(a),this._loading=void 0;case 14:return e.a(2)}}),e,this,[[7,9],[1,3]])}))),function(e){return h.apply(this,arguments)})},{key:"closeDialog",value:function(){if(this._params){var e,t=Boolean(this._step&&["create_entry","abort"].includes(this._step.type));if(!this._step||t||this._params.continueFlowId||this._params.flowConfig.deleteFlow(this.hass,this._step.flow_id),this._step&&this._params.dialogClosedCallback)this._params.dialogClosedCallback({flowFinished:t,entryId:"result"in this._step?null===(e=this._step.result)||void 0===e?void 0:e.entry_id:void 0});this._loading=void 0,this._step=void 0,this._params=void 0,this._handler=void 0,this._unsubDataEntryFlowProgress&&(this._unsubDataEntryFlowProgress(),this._unsubDataEntryFlowProgress=void 0),(0,v.r)(this,"dialog-closed",{dialog:this.localName})}}},{key:"_getDialogTitle",value:function(){var e;if(this._loading||!this._step||!this._params)return"";switch(this._step.type){case"form":return this._params.flowConfig.renderShowFormStepHeader(this.hass,this._step);case"abort":return this._params.flowConfig.renderAbortHeader?this._params.flowConfig.renderAbortHeader(this.hass,this._step):this.hass.localize(`component.${null!==(e=this._params.domain)&&void 0!==e?e:this._step.handler}.title`);case"progress":return this._params.flowConfig.renderShowFormProgressHeader(this.hass,this._step);case"menu":return this._params.flowConfig.renderMenuHeader(this.hass,this._step);case"create_entry":var t,i=this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),null===(t=this._step.result)||void 0===t?void 0:t.entry_id,this._params.carryOverDevices).length;return this.hass.localize("ui.panel.config.integrations.config_flow."+(i?"device_created":"success"),{number:i});default:return""}}},{key:"_getDialogSubtitle",value:function(){var e,t,i,a,r,n,o,s;if(this._loading||!this._step||!this._params)return"";switch(this._step.type){case"form":return null===(e=(t=this._params.flowConfig).renderShowFormStepSubheader)||void 0===e?void 0:e.call(t,this.hass,this._step);case"abort":return null===(i=(a=this._params.flowConfig).renderAbortSubheader)||void 0===i?void 0:i.call(a,this.hass,this._step);case"progress":return null===(r=(n=this._params.flowConfig).renderShowFormProgressSubheader)||void 0===r?void 0:r.call(n,this.hass,this._step);case"menu":return null===(o=(s=this._params.flowConfig).renderMenuSubheader)||void 0===o?void 0:o.call(s,this.hass,this._step);default:return""}}},{key:"render",value:function(){var e,t,i,a,r,n,o;if(!this._params)return p.s6;var s=["form","menu","external","progress","data_entry_flow_progressed"].includes(null===(e=this._step)||void 0===e?void 0:e.type)&&(null===(t=this._params.manifest)||void 0===t?void 0:t.is_built_in)||!(null===(i=this._params.manifest)||void 0===i||!i.documentation),l=this._getDialogTitle(),c=this._getDialogSubtitle();return(0,p.qy)(D||(D=N`
      <ha-dialog
        open
        @closed=${0}
        scrimClickAction
        escapeKeyAction
        hideActions
        .heading=${0}
      >
        <ha-dialog-header slot="heading">
          <ha-icon-button
            .label=${0}
            .path=${0}
            dialogAction="close"
            slot="navigationIcon"
          ></ha-icon-button>

          <div
            slot="title"
            class="dialog-title${0}"
            title=${0}
          >
            ${0}
          </div>

          ${0}
          ${0}
        </ha-dialog-header>
        <div>
          ${0}
        </div>
      </ha-dialog>
    `),this.closeDialog,l||!0,this.hass.localize("ui.common.close"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z","form"===(null===(a=this._step)||void 0===a?void 0:a.type)?" form":"",l,l,c?(0,p.qy)(S||(S=N` <div slot="subtitle">${0}</div>`),c):p.s6,s&&!this._loading&&this._step?(0,p.qy)(F||(F=N`
                <a
                  slot="actionItems"
                  class="help"
                  href=${0}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <ha-icon-button
                    .label=${0}
                    .path=${0}
                  >
                  </ha-icon-button
                ></a>
              `),this._params.manifest.is_built_in?(0,m.o)(this.hass,`/integrations/${this._params.manifest.domain}`):this._params.manifest.documentation,this.hass.localize("ui.common.help"),"M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,9.88 15.64,10.67 15.07,11.25M13,19H11V17H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12C22,6.47 17.5,2 12,2Z"):p.s6,this._loading||null===this._step?(0,p.qy)(q||(q=N`
                <step-flow-loading
                  .flowConfig=${0}
                  .hass=${0}
                  .loadingReason=${0}
                  .handler=${0}
                  .step=${0}
                ></step-flow-loading>
              `),this._params.flowConfig,this.hass,this._loading,this._handler,this._step):void 0===this._step?p.s6:(0,p.qy)(O||(O=N`
                  ${0}
                `),"form"===this._step.type?(0,p.qy)(P||(P=N`
                        <step-flow-form
                          narrow
                          .flowConfig=${0}
                          .step=${0}
                          .hass=${0}
                        ></step-flow-form>
                      `),this._params.flowConfig,this._step,this.hass):"external"===this._step.type?(0,p.qy)(T||(T=N`
                          <step-flow-external
                            .flowConfig=${0}
                            .step=${0}
                            .hass=${0}
                          ></step-flow-external>
                        `),this._params.flowConfig,this._step,this.hass):"abort"===this._step.type?(0,p.qy)(U||(U=N`
                            <step-flow-abort
                              .params=${0}
                              .step=${0}
                              .hass=${0}
                              .handler=${0}
                              .domain=${0}
                            ></step-flow-abort>
                          `),this._params,this._step,this.hass,this._step.handler,null!==(r=this._params.domain)&&void 0!==r?r:this._step.handler):"progress"===this._step.type?(0,p.qy)(Z||(Z=N`
                              <step-flow-progress
                                .flowConfig=${0}
                                .step=${0}
                                .hass=${0}
                                .progress=${0}
                              ></step-flow-progress>
                            `),this._params.flowConfig,this._step,this.hass,this._progress):"menu"===this._step.type?(0,p.qy)(H||(H=N`
                                <step-flow-menu
                                  .flowConfig=${0}
                                  .step=${0}
                                  .hass=${0}
                                ></step-flow-menu>
                              `),this._params.flowConfig,this._step,this.hass):(0,p.qy)(L||(L=N`
                                <step-flow-create-entry
                                  .flowConfig=${0}
                                  .step=${0}
                                  .hass=${0}
                                  .navigateToResult=${0}
                                  .devices=${0}
                                ></step-flow-create-entry>
                              `),this._params.flowConfig,this._step,this.hass,null!==(n=this._params.navigateToResult)&&void 0!==n&&n,this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),null===(o=this._step.result)||void 0===o?void 0:o.entry_id,this._params.carryOverDevices))))}},{key:"firstUpdated",value:function(e){(0,d.A)(t,"firstUpdated",this,3)([e]),this.addEventListener("flow-update",(e=>{var t=e.detail,i=t.step,a=t.stepPromise;this._processStep(i||a)}))}},{key:"willUpdate",value:function(e){(0,d.A)(t,"willUpdate",this,3)([e]),e.has("_step")&&this._step&&["external","progress"].includes(this._step.type)&&this._subscribeDataEntryFlowProgressed()}},{key:"_processStep",value:(a=(0,n.A)((0,r.A)().m((function e(t){var i,a,n,o,s;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(void 0!==t){e.n=1;break}return this.closeDialog(),e.a(2);case 1:return i=setTimeout((()=>{this._loading="loading_step"}),250),e.p=2,e.n=3,t;case 3:a=e.v,e.n=5;break;case 4:return e.p=4,s=e.v,this.closeDialog(),(0,y.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:null==s||null===(n=s.body)||void 0===n?void 0:n.message}),e.a(2);case 5:return e.p=5,clearTimeout(i),this._loading=void 0,e.f(5);case 6:return this._step=void 0,e.n=7,this.updateComplete;case 7:this._step=a,"create_entry"!==a.type&&"abort"!==a.type||!a.next_flow||(this._step=void 0,this._handler=void 0,this._unsubDataEntryFlowProgress&&(this._unsubDataEntryFlowProgress(),this._unsubDataEntryFlowProgress=void 0),"config_flow"===a.next_flow[0]?(0,z.W)(this,{continueFlowId:a.next_flow[1],carryOverDevices:this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),"create_entry"===a.type?null===(o=a.result)||void 0===o?void 0:o.entry_id:void 0,this._params.carryOverDevices).map((e=>e.id)),dialogClosedCallback:this._params.dialogClosedCallback}):"options_flow"===a.next_flow[0]?"create_entry"===a.type&&(0,C.Q)(this,a.result,{continueFlowId:a.next_flow[1],navigateToResult:this._params.navigateToResult,dialogClosedCallback:this._params.dialogClosedCallback}):"config_subentries_flow"===a.next_flow[0]?"create_entry"===a.type&&(0,M.a)(this,a.result,a.next_flow[0],{continueFlowId:a.next_flow[1],navigateToResult:this._params.navigateToResult,dialogClosedCallback:this._params.dialogClosedCallback}):(this.closeDialog(),(0,y.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error",{error:`Unsupported next flow type: ${a.next_flow[0]}`})})));case 8:return e.a(2)}}),e,this,[[2,4,5,6]])}))),function(e){return a.apply(this,arguments)})},{key:"_subscribeDataEntryFlowProgressed",value:(i=(0,n.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(!this._unsubDataEntryFlowProgress){e.n=1;break}return e.a(2);case 1:this._progress=void 0,t=[(0,g.P)(this.hass.connection,(e=>{var t;e.data.flow_id===(null===(t=this._step)||void 0===t?void 0:t.flow_id)&&(this._processStep(this._params.flowConfig.fetchFlow(this.hass,this._step.flow_id)),this._progress=void 0)})),(0,g.K)(this.hass.connection,(e=>{this._progress=Math.ceil(100*e.data.progress)}))],this._unsubDataEntryFlowProgress=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,Promise.all(t);case 1:e.v.map((e=>e()));case 2:return e.a(2)}}),e)})));case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})}],[{key:"styles",get:function(){return[_.nA,(0,p.AH)(j||(j=N`
        ha-dialog {
          --dialog-content-padding: 0;
        }
        .dialog-title {
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .dialog-title.form {
          white-space: normal;
        }
        .help {
          color: var(--secondary-text-color);
        }
      `))]}}]);var i,a,h}(p.WF);(0,h.__decorate)([(0,u.MZ)({attribute:!1})],B.prototype,"hass",void 0),(0,h.__decorate)([(0,u.wk)()],B.prototype,"_params",void 0),(0,h.__decorate)([(0,u.wk)()],B.prototype,"_loading",void 0),(0,h.__decorate)([(0,u.wk)()],B.prototype,"_progress",void 0),(0,h.__decorate)([(0,u.wk)()],B.prototype,"_step",void 0),(0,h.__decorate)([(0,u.wk)()],B.prototype,"_handler",void 0),B=(0,h.__decorate)([(0,u.EM)("dialog-data-entry-flow")],B),a()}catch(W){a(W)}}))},73042:function(e,t,i){"use strict";i.d(t,{W:function(){return w}});var a,r,n,o,s,l,c,d,h,p=i(61397),u=i(78261),f=i(50264),v=(i(52675),i(89463),i(23792),i(26099),i(3362),i(62953),i(96196)),g=i(23608),_=i(84125),m=i(73347),y=e=>e,w=(e,t)=>{return(0,m.g)(e,t,{flowType:"config_flow",showDevices:!0,createFlow:(w=(0,f.A)((0,p.A)().m((function e(i,a){var r,n,o;return(0,p.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,Promise.all([(0,g.t1)(i,a,t.entryId),i.loadFragmentTranslation("config"),i.loadBackendTranslation("config",a),i.loadBackendTranslation("selector",a),i.loadBackendTranslation("title",a)]);case 1:return r=e.v,n=(0,u.A)(r,1),o=n[0],e.a(2,o)}}),e)}))),function(e,t){return w.apply(this,arguments)}),fetchFlow:(i=(0,f.A)((0,p.A)().m((function e(t,i){var a,r,n;return(0,p.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,Promise.all([(0,g.PN)(t,i),t.loadFragmentTranslation("config")]);case 1:return a=e.v,r=(0,u.A)(a,1),n=r[0],e.n=2,Promise.all([t.loadBackendTranslation("config",n.handler),t.loadBackendTranslation("selector",n.handler),t.loadBackendTranslation("title",n.handler)]);case 2:return e.a(2,n)}}),e)}))),function(e,t){return i.apply(this,arguments)}),handleFlowStep:g.jm,deleteFlow:g.sR,renderAbortDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.abort.${t.reason}`,t.description_placeholders);return i?(0,v.qy)(a||(a=y`
            <ha-markdown allow-svg breaks .content=${0}></ha-markdown>
          `),i):t.reason},renderShowFormStepHeader(e,t){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.title`,t.description_placeholders)||e.localize(`component.${t.handler}.title`)},renderShowFormStepDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.description`,t.description_placeholders);return i?(0,v.qy)(r||(r=y`
            <ha-markdown
              .allowDataUrl=${0}
              allow-svg
              breaks
              .content=${0}
            ></ha-markdown>
          `),"zwave_js"===t.handler,i):""},renderShowFormStepFieldLabel(e,t,i,a){var r;if("expandable"===i.type)return e.localize(`component.${t.handler}.config.step.${t.step_id}.sections.${i.name}.name`,t.description_placeholders);var n=null!=a&&null!==(r=a.path)&&void 0!==r&&r[0]?`sections.${a.path[0]}.`:"";return e.localize(`component.${t.handler}.config.step.${t.step_id}.${n}data.${i.name}`,t.description_placeholders)||i.name},renderShowFormStepFieldHelper(e,t,i,a){var r;if("expandable"===i.type)return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.sections.${i.name}.description`,t.description_placeholders);var o=null!=a&&null!==(r=a.path)&&void 0!==r&&r[0]?`sections.${a.path[0]}.`:"",s=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.${o}data_description.${i.name}`,t.description_placeholders);return s?(0,v.qy)(n||(n=y`<ha-markdown breaks .content=${0}></ha-markdown>`),s):""},renderShowFormStepFieldError(e,t,i){return e.localize(`component.${t.translation_domain||t.translation_domain||t.handler}.config.error.${i}`,t.description_placeholders)||i},renderShowFormStepFieldLocalizeValue(e,t,i){return e.localize(`component.${t.handler}.selector.${i}`)},renderShowFormStepSubmitButton(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.submit`)||e.localize("ui.panel.config.integrations.config_flow."+(!1===t.last_step?"next":"submit"))},renderExternalStepHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize("ui.panel.config.integrations.config_flow.external_step.open_site")},renderExternalStepDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.${t.step_id}.description`,t.description_placeholders);return(0,v.qy)(o||(o=y`
        <p>
          ${0}
        </p>
        ${0}
      `),e.localize("ui.panel.config.integrations.config_flow.external_step.description"),i?(0,v.qy)(s||(s=y`
              <ha-markdown
                allow-svg
                breaks
                .content=${0}
              ></ha-markdown>
            `),i):"")},renderCreateEntryDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.create_entry.${t.description||"default"}`,t.description_placeholders);return(0,v.qy)(l||(l=y`
        ${0}
      `),i?(0,v.qy)(c||(c=y`
              <ha-markdown
                allow-svg
                breaks
                .content=${0}
              ></ha-markdown>
            `),i):v.s6)},renderShowFormProgressHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize(`component.${t.handler}.title`)},renderShowFormProgressDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.progress.${t.progress_action}`,t.description_placeholders);return i?(0,v.qy)(d||(d=y`
            <ha-markdown allow-svg breaks .content=${0}></ha-markdown>
          `),i):""},renderMenuHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize(`component.${t.handler}.title`)},renderMenuDescription(e,t){var i=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.description`,t.description_placeholders);return i?(0,v.qy)(h||(h=y`
            <ha-markdown allow-svg breaks .content=${0}></ha-markdown>
          `),i):""},renderMenuOption(e,t,i){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.menu_options.${i}`,t.description_placeholders)},renderMenuOptionDescription(e,t,i){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.menu_option_descriptions.${i}`,t.description_placeholders)},renderLoadingDescription(e,t,i,a){if("loading_flow"!==t&&"loading_step"!==t)return"";var r=(null==a?void 0:a.handler)||i;return e.localize(`ui.panel.config.integrations.config_flow.loading.${t}`,{integration:r?(0,_.p$)(e.localize,r):e.localize("ui.panel.config.integrations.config_flow.loading.fallback_title")})}});var i,w}},93056:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),n=i(44734),o=i(56038),s=i(69683),l=i(25460),c=i(6454),d=i(62826),h=i(96196),p=i(77845),u=i(92542),f=i(78778),v=i(73042),g=i(97854),_=i(89473),m=e([_]);_=(m.then?(await m)():m)[0];var y,w=e=>e,b=function(e){function t(){return(0,n.A)(this,t),(0,s.A)(this,t,arguments)}return(0,c.A)(t,e),(0,o.A)(t,[{key:"firstUpdated",value:function(e){(0,l.A)(t,"firstUpdated",this,3)([e]),"missing_credentials"===this.step.reason&&this._handleMissingCreds()}},{key:"render",value:function(){return"missing_credentials"===this.step.reason?h.s6:(0,h.qy)(y||(y=w`
      <div class="content">
        ${0}
      </div>
      <div class="buttons">
        <ha-button appearance="plain" @click=${0}
          >${0}</ha-button
        >
      </div>
    `),this.params.flowConfig.renderAbortDescription(this.hass,this.step),this._flowDone,this.hass.localize("ui.panel.config.integrations.config_flow.close"))}},{key:"_handleMissingCreds",value:(i=(0,r.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:(0,f.a)(this.params.dialogParentElement,{selectedDomain:this.domain,manifest:this.params.manifest,applicationCredentialAddedCallback:()=>{var e;(0,v.W)(this.params.dialogParentElement,{dialogClosedCallback:this.params.dialogClosedCallback,startFlowHandler:this.handler,showAdvanced:null===(e=this.hass.userData)||void 0===e?void 0:e.showAdvanced,navigateToResult:this.params.navigateToResult})}}),this._flowDone();case 1:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_flowDone",value:function(){(0,u.r)(this,"flow-update",{step:void 0})}}],[{key:"styles",get:function(){return g.G}}]);var i}(h.WF);(0,d.__decorate)([(0,p.MZ)({attribute:!1})],b.prototype,"params",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],b.prototype,"step",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],b.prototype,"domain",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],b.prototype,"handler",void 0),b=(0,d.__decorate)([(0,p.EM)("step-flow-abort")],b),t()}catch(k){t(k)}}))},64533:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(94741),r=i(78261),n=i(61397),o=i(50264),s=i(44734),l=i(56038),c=i(69683),d=i(6454),h=i(25460),p=(i(28706),i(2008),i(74423),i(23792),i(62062),i(44114),i(18111),i(22489),i(7588),i(61701),i(13579),i(5506),i(53921),i(26099),i(16034),i(3362),i(96167),i(23500),i(62953),i(62826)),u=i(96196),f=i(77845),v=i(22786),g=i(92542),_=i(16727),m=i(41144),y=i(5871),w=i(53907),b=i(89473),k=i(41558),$=i(1491),A=i(22800),x=i(84125),C=i(76681),M=i(10234),z=i(6358),E=i(97854),D=i(3950),S=e([w,b]);[w,b]=S.then?(await S)():S;var F,q,O,P,T,U,Z,H,L=e=>e,j=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(a)))._domains={},e.navigateToResult=!1,e._deviceUpdate={},e._deviceEntities=(0,v.A)(((e,t,i)=>t.filter((t=>t.device_id===e&&(!i||(0,m.m)(t.entity_id)===i))))),e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"firstUpdated",value:function(e){(0,h.A)(t,"firstUpdated",this,3)([e]),this._loadDomains()}},{key:"willUpdate",value:function(e){var t;if((e.has("devices")||e.has("hass"))&&1===this.devices.length&&this.devices[0].primary_config_entry===(null===(t=this.step.result)||void 0===t?void 0:t.entry_id)&&"voip"!==this.step.result.domain){var i=this._deviceEntities(this.devices[0].id,Object.values(this.hass.entities),"assist_satellite");i.length&&i.some((e=>(0,k.KC)(this.hass.states[e.entity_id])))&&(this.navigateToResult=!1,this._flowDone(),(0,z.L)(this,{deviceId:this.devices[0].id}))}}},{key:"render",value:function(){var e,t=this.hass.localize,i=this.step.result?Object.assign(Object.assign({},this._domains),{},{[this.step.result.entry_id]:this.step.result.domain}):this._domains;return(0,u.qy)(F||(F=L`
      <div class="content">
        ${0}
        ${0}
        ${0}
      </div>
      <div class="buttons">
        <ha-button @click=${0}
          >${0}</ha-button
        >
      </div>
    `),this.flowConfig.renderCreateEntryDescription(this.hass,this.step),"not_loaded"===(null===(e=this.step.result)||void 0===e?void 0:e.state)?(0,u.qy)(q||(q=L`<span class="error"
              >${0}</span
            >`),t("ui.panel.config.integrations.config_flow.not_loaded")):u.s6,0===this.devices.length&&["options_flow","repair_flow"].includes(this.flowConfig.flowType)?u.s6:0===this.devices.length?(0,u.qy)(O||(O=L`<p>
                ${0}
              </p>`),t("ui.panel.config.integrations.config_flow.created_config",{name:this.step.title})):(0,u.qy)(P||(P=L`
                <div class="devices">
                  ${0}
                </div>
              `),this.devices.map((e=>{var a,r,n,o,s,l;return(0,u.qy)(T||(T=L`
                      <div class="device">
                        <div class="device-info">
                          ${0}
                          <div class="device-info-details">
                            <span>${0}</span>
                            ${0}
                          </div>
                        </div>
                        <ha-textfield
                          .label=${0}
                          .placeholder=${0}
                          .value=${0}
                          @change=${0}
                          .device=${0}
                        ></ha-textfield>
                        <ha-area-picker
                          .hass=${0}
                          .device=${0}
                          .value=${0}
                          @value-changed=${0}
                        ></ha-area-picker>
                      </div>
                    `),e.primary_config_entry&&i[e.primary_config_entry]?(0,u.qy)(U||(U=L`<img
                                slot="graphic"
                                alt=${0}
                                src=${0}
                                crossorigin="anonymous"
                                referrerpolicy="no-referrer"
                              />`),(0,x.p$)(this.hass.localize,i[e.primary_config_entry]),(0,C.MR)({domain:i[e.primary_config_entry],type:"icon",darkOptimized:null===(a=this.hass.themes)||void 0===a?void 0:a.darkMode})):u.s6,e.model||e.manufacturer,e.model?(0,u.qy)(Z||(Z=L`<span class="secondary">
                                  ${0}
                                </span>`),e.manufacturer):u.s6,t("ui.panel.config.integrations.config_flow.device_name"),(0,_.T)(e,this.hass),null!==(r=null===(n=this._deviceUpdate[e.id])||void 0===n?void 0:n.name)&&void 0!==r?r:(0,_.xn)(e),this._deviceNameChanged,e.id,this.hass,e.id,null!==(o=null!==(s=null===(l=this._deviceUpdate[e.id])||void 0===l?void 0:l.area)&&void 0!==s?s:e.area_id)&&void 0!==o?o:void 0,this._areaPicked)}))),this._flowDone,t("ui.panel.config.integrations.config_flow."+(!this.devices.length||Object.keys(this._deviceUpdate).length?"finish":"finish_skip")))}},{key:"_loadDomains",value:(f=(0,o.A)((0,n.A)().m((function e(){var t;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,D.VN)(this.hass);case 1:t=e.v,this._domains=Object.fromEntries(t.map((e=>[e.entry_id,e.domain])));case 2:return e.a(2)}}),e,this)}))),function(){return f.apply(this,arguments)})},{key:"_flowDone",value:(p=(0,o.A)((0,n.A)().m((function e(){var t,i,o,s,l;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:if(!Object.keys(this._deviceUpdate).length){e.n=3;break}return t=[],i=Object.entries(this._deviceUpdate).map((e=>{var i=(0,r.A)(e,2),a=i[0],n=i[1];return n.name&&t.push(a),(0,$.FB)(this.hass,a,{name_by_user:n.name,area_id:n.area}).catch((e=>{(0,M.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error_saving_device",{error:e.message})})}))})),e.n=1,Promise.allSettled(i);case 1:return o=[],s=[],t.forEach((e=>{var t=this._deviceEntities(e,Object.values(this.hass.entities));s.push.apply(s,(0,a.A)(t.map((e=>e.entity_id))))})),e.n=2,(0,A.BM)(this.hass,s);case 2:return l=e.v,Object.entries(l).forEach((e=>{var t=(0,r.A)(e,2),i=t[0],a=t[1];a&&o.push((0,A.G_)(this.hass,i,{new_entity_id:a}).catch((e=>(0,M.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error_saving_entity",{error:e.message})}))))})),e.n=3,Promise.allSettled(o);case 3:(0,g.r)(this,"flow-update",{step:void 0}),this.step.result&&this.navigateToResult&&(1===this.devices.length?(0,y.o)(`/config/devices/device/${this.devices[0].id}`):(0,y.o)(`/config/integrations/integration/${this.step.result.domain}#config_entry=${this.step.result.entry_id}`));case 4:return e.a(2)}}),e,this)}))),function(){return p.apply(this,arguments)})},{key:"_areaPicked",value:(i=(0,o.A)((0,n.A)().m((function e(t){var i,a,r;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:i=t.currentTarget,a=i.device,r=t.detail.value,a in this._deviceUpdate||(this._deviceUpdate[a]={}),this._deviceUpdate[a].area=r,this.requestUpdate("_deviceUpdate");case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_deviceNameChanged",value:function(e){var t=e.currentTarget,i=t.device,a=t.value;i in this._deviceUpdate||(this._deviceUpdate[i]={}),this._deviceUpdate[i].name=a,this.requestUpdate("_deviceUpdate")}}],[{key:"styles",get:function(){return[E.G,(0,u.AH)(H||(H=L`
        .devices {
          display: flex;
          margin: -4px;
          max-height: 600px;
          overflow-y: auto;
          flex-direction: column;
        }
        @media all and (max-width: 450px), all and (max-height: 500px) {
          .devices {
            /* header - margin content - footer */
            max-height: calc(100vh - 52px - 20px - 52px);
          }
        }
        .device {
          border: 1px solid var(--divider-color);
          padding: 6px;
          border-radius: var(--ha-border-radius-sm);
          margin: 4px;
          display: inline-block;
        }
        .device-info {
          display: flex;
          align-items: center;
          gap: var(--ha-space-2);
        }
        .device-info img {
          width: 40px;
          height: 40px;
        }
        .device-info-details {
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        .secondary {
          color: var(--secondary-text-color);
        }
        ha-textfield,
        ha-area-picker {
          display: block;
        }
        ha-textfield {
          margin: 8px 0;
        }
        .buttons > *:last-child {
          margin-left: auto;
          margin-inline-start: auto;
          margin-inline-end: initial;
        }
        .error {
          color: var(--error-color);
        }
      `))]}}]);var i,p,f}(u.WF);(0,p.__decorate)([(0,f.MZ)({attribute:!1})],j.prototype,"flowConfig",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:!1})],j.prototype,"hass",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:!1})],j.prototype,"step",void 0),(0,p.__decorate)([(0,f.MZ)({attribute:!1})],j.prototype,"devices",void 0),(0,p.__decorate)([(0,f.wk)()],j.prototype,"_deviceUpdate",void 0),j=(0,p.__decorate)([(0,f.EM)("step-flow-create-entry")],j),t()}catch(N){t(N)}}))},12083:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),n=i(69683),o=i(25460),s=i(6454),l=i(62826),c=i(96196),d=i(77845),h=i(97854),p=i(89473),u=e([p]);p=(u.then?(await u)():u)[0];var f,v,g=e=>e,_=function(e){function t(){return(0,a.A)(this,t),(0,n.A)(this,t,arguments)}return(0,s.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=this.hass.localize;return(0,c.qy)(f||(f=g`
      <div class="content">
        ${0}
        <div class="open-button">
          <ha-button href=${0} target="_blank" rel="noreferrer">
            ${0}
          </ha-button>
        </div>
      </div>
    `),this.flowConfig.renderExternalStepDescription(this.hass,this.step),this.step.url,e("ui.panel.config.integrations.config_flow.external_step.open_site"))}},{key:"firstUpdated",value:function(e){(0,o.A)(t,"firstUpdated",this,3)([e]),window.open(this.step.url)}}],[{key:"styles",get:function(){return[h.G,(0,c.AH)(v||(v=g`
        .open-button {
          text-align: center;
          padding: 24px 0;
        }
        .open-button a {
          text-decoration: none;
        }
      `))]}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],_.prototype,"flowConfig",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],_.prototype,"step",void 0),_=(0,l.__decorate)([(0,d.EM)("step-flow-external")],_),t()}catch(m){t(m)}}))},84398:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),n=i(44734),o=i(56038),s=i(69683),l=i(6454),c=i(25460),d=(i(28706),i(50113),i(74423),i(23792),i(62062),i(18111),i(81148),i(20116),i(7588),i(61701),i(26099),i(16034),i(3362),i(23500),i(62953),i(62826)),h=i(96196),p=i(77845),u=i(22786),f=i(51757),v=i(92542),g=i(45817),_=i(89473),m=(i(17963),i(23442)),y=(i(91120),i(28089),i(89600)),w=i(54193),b=i(73103),k=i(39396),$=i(97854),A=e([_,y]);[_,y]=A.then?(await A)():A;var x,C,M,z,E=e=>e,D=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).narrow=!1,e._loading=!1,e.handleReadOnlyFields=(0,u.A)((e=>null==e?void 0:e.map((e=>{var t,i;return Object.assign(Object.assign({},e),null!==(t=Object.values(null!==(i=null==e?void 0:e.selector)&&void 0!==i?i:{})[0])&&void 0!==t&&t.read_only?{disabled:!0}:{})})))),e._handleKeyDown=t=>{"Enter"===t.key&&e._submitStep()},e._labelCallback=(t,i,a)=>e.flowConfig.renderShowFormStepFieldLabel(e.hass,e.step,t,a),e._helperCallback=(t,i)=>e.flowConfig.renderShowFormStepFieldHelper(e.hass,e.step,t,i),e._errorCallback=t=>e.flowConfig.renderShowFormStepFieldError(e.hass,e.step,t),e._localizeValueCallback=t=>e.flowConfig.renderShowFormStepFieldLocalizeValue(e.hass,e.step,t),e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"disconnectedCallback",value:function(){(0,c.A)(t,"disconnectedCallback",this,3)([]),this.removeEventListener("keydown",this._handleKeyDown)}},{key:"render",value:function(){var e=this.step,t=this._stepDataProcessed;return(0,h.qy)(x||(x=E`
      <div class="content" @click=${0}>
        ${0}
        ${0}
        <ha-form
          .hass=${0}
          .narrow=${0}
          .data=${0}
          .disabled=${0}
          @value-changed=${0}
          .schema=${0}
          .error=${0}
          .computeLabel=${0}
          .computeHelper=${0}
          .computeError=${0}
          .localizeValue=${0}
        ></ha-form>
      </div>
      ${0}
      <div class="buttons">
        <ha-button @click=${0} .loading=${0}>
          ${0}
        </ha-button>
      </div>
    `),this._clickHandler,this.flowConfig.renderShowFormStepDescription(this.hass,this.step),this._errorMsg?(0,h.qy)(C||(C=E`<ha-alert alert-type="error">${0}</ha-alert>`),this._errorMsg):"",this.hass,this.narrow,t,this._loading,this._stepDataChanged,(0,w.Hg)(this.handleReadOnlyFields(e.data_schema)),this._errors,this._labelCallback,this._helperCallback,this._errorCallback,this._localizeValueCallback,e.preview?(0,h.qy)(M||(M=E`<div class="preview" @set-flow-errors=${0}>
            <h3>
              ${0}:
            </h3>
            ${0}
          </div>`),this._setError,this.hass.localize("ui.panel.config.integrations.config_flow.preview"),(0,f._)(`flow-preview-${(0,b.F)(e.preview)}`,{hass:this.hass,domain:e.preview,flowType:this.flowConfig.flowType,handler:e.handler,stepId:e.step_id,flowId:e.flow_id,stepData:t})):h.s6,this._submitStep,this._loading,this.flowConfig.renderShowFormStepSubmitButton(this.hass,this.step))}},{key:"_setError",value:function(e){this._previewErrors=e.detail}},{key:"firstUpdated",value:function(e){(0,c.A)(t,"firstUpdated",this,3)([e]),setTimeout((()=>this.shadowRoot.querySelector("ha-form").focus()),0),this.addEventListener("keydown",this._handleKeyDown)}},{key:"willUpdate",value:function(e){var a;(0,c.A)(t,"willUpdate",this,3)([e]),e.has("step")&&null!==(a=this.step)&&void 0!==a&&a.preview&&i(25115)(`./flow-preview-${(0,b.F)(this.step.preview)}`),(e.has("step")||e.has("_previewErrors")||e.has("_submitErrors"))&&(this._errors=this.step.errors||this._previewErrors||this._submitErrors?Object.assign(Object.assign(Object.assign({},this.step.errors),this._previewErrors),this._submitErrors):void 0)}},{key:"_clickHandler",value:function(e){(0,g.d)(e,!1)&&(0,v.r)(this,"flow-update",{step:void 0})}},{key:"_stepDataProcessed",get:function(){return void 0!==this._stepData||(this._stepData=(0,m.$)(this.step.data_schema)),this._stepData}},{key:"_submitStep",value:(d=(0,r.A)((0,a.A)().m((function e(){var t,i,r,n,o,s;return(0,a.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(t=this._stepData||{},i=(e,t)=>e.every((e=>(!e.required||!["",void 0].includes(t[e.name]))&&("expandable"!==e.type||!e.required&&void 0===t[e.name]||i(e.schema,t[e.name])))),void 0===t?void 0===this.step.data_schema.find((e=>e.required)):i(this.step.data_schema,t)){e.n=1;break}return this._errorMsg=this.hass.localize("ui.panel.config.integrations.config_flow.not_all_required_fields"),e.a(2);case 1:return this._loading=!0,this._errorMsg=void 0,this._submitErrors=void 0,r=this.step.flow_id,n={},Object.keys(t).forEach((e=>{var i,a,r,o=t[e],s=[void 0,""].includes(o),l=null===(i=this.step.data_schema)||void 0===i?void 0:i.find((t=>t.name===e)),c=null!==(a=null==l?void 0:l.selector)&&void 0!==a?a:{},d=null===(r=Object.values(c)[0])||void 0===r?void 0:r.read_only;s||d||(n[e]=o)})),e.p=2,e.n=3,this.flowConfig.handleFlowStep(this.hass,this.step.flow_id,n);case 3:if(o=e.v,this.step&&r===this.step.flow_id){e.n=4;break}return e.a(2);case 4:this._previewErrors=void 0,(0,v.r)(this,"flow-update",{step:o}),e.n=6;break;case 5:e.p=5,(s=e.v)&&s.body?(s.body.message&&(this._errorMsg=s.body.message),s.body.errors&&(this._submitErrors=s.body.errors),s.body.message||s.body.errors||(this._errorMsg="Unknown error occurred")):this._errorMsg="Unknown error occurred";case 6:return e.p=6,this._loading=!1,e.f(6);case 7:return e.a(2)}}),e,this,[[2,5,6,7]])}))),function(){return d.apply(this,arguments)})},{key:"_stepDataChanged",value:function(e){this._stepData=e.detail.value}}],[{key:"styles",get:function(){return[k.RF,$.G,(0,h.AH)(z||(z=E`
        .error {
          color: red;
        }

        ha-alert,
        ha-form {
          margin-top: 24px;
          display: block;
        }

        .buttons {
          padding: 16px;
        }
      `))]}}]);var d}(h.WF);(0,d.__decorate)([(0,p.MZ)({attribute:!1})],D.prototype,"flowConfig",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],D.prototype,"narrow",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],D.prototype,"step",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],D.prototype,"hass",void 0),(0,d.__decorate)([(0,p.wk)()],D.prototype,"_loading",void 0),(0,d.__decorate)([(0,p.wk)()],D.prototype,"_stepData",void 0),(0,d.__decorate)([(0,p.wk)()],D.prototype,"_previewErrors",void 0),(0,d.__decorate)([(0,p.wk)()],D.prototype,"_submitErrors",void 0),(0,d.__decorate)([(0,p.wk)()],D.prototype,"_errorMsg",void 0),D=(0,d.__decorate)([(0,p.EM)("step-flow-form")],D),t()}catch(S){t(S)}}))},19486:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),n=i(69683),o=i(6454),s=i(62826),l=i(96196),c=i(77845),d=i(89600),h=e([d]);d=(h.then?(await h)():h)[0];var p,u,f,v=e=>e,g=function(e){function t(){return(0,a.A)(this,t),(0,n.A)(this,t,arguments)}return(0,o.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=this.flowConfig.renderLoadingDescription(this.hass,this.loadingReason,this.handler,this.step);return(0,l.qy)(p||(p=v`
      <div class="content">
        <ha-spinner size="large"></ha-spinner>
        ${0}
      </div>
    `),e?(0,l.qy)(u||(u=v`<div>${0}</div>`),e):"")}}])}(l.WF);g.styles=(0,l.AH)(f||(f=v`
    .content {
      margin-top: 0;
      padding: 50px 100px;
      text-align: center;
    }
    ha-spinner {
      margin-bottom: 16px;
    }
  `)),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"flowConfig",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"loadingReason",void 0),(0,s.__decorate)([(0,c.MZ)()],g.prototype,"handler",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"step",void 0),g=(0,s.__decorate)([(0,c.EM)("step-flow-loading")],g),t()}catch(_){t(_)}}))},59395:function(e,t,i){"use strict";var a,r,n,o,s,l=i(31432),c=i(44734),d=i(56038),h=i(69683),p=i(6454),u=(i(23792),i(62062),i(26910),i(18111),i(61701),i(53921),i(26099),i(62826)),f=i(96196),v=i(77845),g=i(92542),_=(i(28608),i(56565),i(97854)),m=i(25749),y=e=>e,w=function(e){function t(){return(0,c.A)(this,t),(0,h.A)(this,t,arguments)}return(0,p.A)(t,e),(0,d.A)(t,[{key:"shouldUpdate",value:function(e){var t;return e.size>1||!e.has("hass")||this.hass.localize!==(null===(t=e.get("hass"))||void 0===t?void 0:t.localize)}},{key:"render",value:function(){var e,t,i={};if(Array.isArray(this.step.menu_options)){e=this.step.menu_options,t={};var s,c=(0,l.A)(e);try{for(c.s();!(s=c.n()).done;){var d=s.value;t[d]=this.flowConfig.renderMenuOption(this.hass,this.step,d),i[d]=this.flowConfig.renderMenuOptionDescription(this.hass,this.step,d)}}catch(p){c.e(p)}finally{c.f()}}else e=Object.keys(this.step.menu_options),t=this.step.menu_options,i=Object.fromEntries(e.map((e=>[e,this.flowConfig.renderMenuOptionDescription(this.hass,this.step,e)])));this.step.sort&&(e=e.sort(((e,i)=>(0,m.xL)(t[e],t[i],this.hass.locale.language))));var h=this.flowConfig.renderMenuDescription(this.hass,this.step);return(0,f.qy)(a||(a=y`
      ${0}
      <div class="options">
        ${0}
      </div>
    `),h?(0,f.qy)(r||(r=y`<div class="content">${0}</div>`),h):"",e.map((e=>(0,f.qy)(n||(n=y`
            <ha-list-item
              hasMeta
              .step=${0}
              @click=${0}
              ?twoline=${0}
              ?multiline-secondary=${0}
            >
              <span>${0}</span>
              ${0}
              <ha-icon-next slot="meta"></ha-icon-next>
            </ha-list-item>
          `),e,this._handleStep,i[e],i[e],t[e],i[e]?(0,f.qy)(o||(o=y`<span slot="secondary">
                    ${0}
                  </span>`),i[e]):f.s6))))}},{key:"_handleStep",value:function(e){(0,g.r)(this,"flow-update",{stepPromise:this.flowConfig.handleFlowStep(this.hass,this.step.flow_id,{next_step_id:e.currentTarget.step})})}}])}(f.WF);w.styles=[_.G,(0,f.AH)(s||(s=y`
      .options {
        margin-top: 20px;
        margin-bottom: 16px;
      }
      .content {
        padding-bottom: 16px;
      }
      .content + .options {
        margin-top: 8px;
      }
      ha-list-item {
        --mdc-list-side-padding: 24px;
      }
    `))],(0,u.__decorate)([(0,v.MZ)({attribute:!1})],w.prototype,"flowConfig",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],w.prototype,"step",void 0),w=(0,u.__decorate)([(0,v.EM)("step-flow-menu")],w)},12527:function(e,t,i){"use strict";i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),n=i(69683),o=i(6454),s=(i(2892),i(62826)),l=i(96196),c=i(77845),d=i(48565),h=i(64109),p=i(89600),u=i(97854),f=e([h,p]);[h,p]=f.then?(await f)():f;var v,g,_,m,y=e=>e,w=function(e){function t(){return(0,a.A)(this,t),(0,n.A)(this,t,arguments)}return(0,o.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,l.qy)(v||(v=y`
      <div class="content">
        ${0}
        ${0}
      </div>
    `),this.progress?(0,l.qy)(g||(g=y`
              <ha-progress-ring .value=${0} size="large"
                >${0}${0}%</ha-progress-ring
              >
            `),this.progress,this.progress,(0,d.d)(this.hass.locale)):(0,l.qy)(_||(_=y`<ha-spinner size="large"></ha-spinner>`)),this.flowConfig.renderShowFormProgressDescription(this.hass,this.step))}}],[{key:"styles",get:function(){return[u.G,(0,l.AH)(m||(m=y`
        .content {
          margin-top: 0;
          padding: 50px 100px;
          text-align: center;
        }
        ha-spinner {
          margin-bottom: 16px;
        }
      `))]}}])}(l.WF);(0,s.__decorate)([(0,c.MZ)({attribute:!1})],w.prototype,"flowConfig",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],w.prototype,"step",void 0),(0,s.__decorate)([(0,c.MZ)({type:Number})],w.prototype,"progress",void 0),w=(0,s.__decorate)([(0,c.EM)("step-flow-progress")],w),t()}catch(b){t(b)}}))},97854:function(e,t,i){"use strict";i.d(t,{G:function(){return r}});var a,r=(0,i(96196).AH)(a||(a=(e=>e)`
  h2 {
    margin: 24px 38px 0 0;
    margin-inline-start: 0px;
    margin-inline-end: 38px;
    padding: 0 24px;
    padding-inline-start: 24px;
    padding-inline-end: 24px;
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    font-family: var(
      --mdc-typography-headline6-font-family,
      var(--mdc-typography-font-family, var(--ha-font-family-body))
    );
    font-size: var(--mdc-typography-headline6-font-size, var(--ha-font-size-l));
    line-height: var(--mdc-typography-headline6-line-height, 2rem);
    font-weight: var(
      --mdc-typography-headline6-font-weight,
      var(--ha-font-weight-medium)
    );
    letter-spacing: var(--mdc-typography-headline6-letter-spacing, 0.0125em);
    text-decoration: var(--mdc-typography-headline6-text-decoration, inherit);
    text-transform: var(--mdc-typography-headline6-text-transform, inherit);
    box-sizing: border-box;
  }

  .content,
  .preview {
    margin-top: 20px;
    padding: 0 24px;
  }

  .buttons {
    position: relative;
    padding: 16px;
    margin: 8px 0 0;
    color: var(--primary-color);
    display: flex;
    justify-content: flex-end;
  }

  ha-markdown {
    overflow-wrap: break-word;
  }
  ha-markdown a {
    color: var(--primary-color);
  }
  ha-markdown img:first-child:last-child {
    display: block;
    margin: 0 auto;
  }
`))},6358:function(e,t,i){"use strict";i.d(t,{L:function(){return n}});i(23792),i(26099),i(3362),i(62953);var a=i(92542),r=()=>Promise.all([i.e("2016"),i.e("3806"),i.e("5629"),i.e("5633"),i.e("1283"),i.e("2097")]).then(i.bind(i,54728)),n=(e,t)=>{(0,a.r)(e,"show-dialog",{dialogTag:"ha-voice-assistant-setup-dialog",dialogImport:r,dialogParams:t})}},78778:function(e,t,i){"use strict";i.d(t,{a:function(){return n}});i(23792),i(26099),i(3362),i(62953);var a=i(92542),r=()=>Promise.all([i.e("7255"),i.e("8451")]).then(i.bind(i,71614)),n=(e,t)=>{(0,a.r)(e,"show-dialog",{dialogTag:"dialog-add-application-credential",dialogImport:r,dialogParams:t})}},76681:function(e,t,i){"use strict";i.d(t,{MR:function(){return a},a_:function(){return r},bg:function(){return n}});var a=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,r=e=>e.split("/")[4],n=e=>e.startsWith("https://brands.home-assistant.io/")},62001:function(e,t,i){"use strict";i.d(t,{o:function(){return a}});i(74423);var a=(e,t)=>`https://${e.config.version.includes("b")?"rc":e.config.version.includes("dev")?"next":"www"}.home-assistant.io${t}`},3164:function(e,t,i){"use strict";i.d(t,{A:function(){return r}});i(52675),i(89463),i(16280),i(23792),i(26099),i(62953);var a=i(47075);function r(e){if(null!=e){var t=e["function"==typeof Symbol&&Symbol.iterator||"@@iterator"],i=0;if(t)return t.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length))return{next:function(){return e&&i>=e.length&&(e=void 0),{value:e&&e[i++],done:!e}}}}throw new TypeError((0,a.A)(e)+" is not iterable")}},2355:function(e,t,i){"use strict";var a,r=i(96196);t.A=(0,r.AH)(a||(a=(e=>e)`:host {
  --size: 8rem;
  --track-width: 0.25em;
  --track-color: var(--wa-color-neutral-fill-normal);
  --indicator-width: var(--track-width);
  --indicator-color: var(--wa-color-brand-fill-loud);
  --indicator-transition-duration: 0.35s;
  display: inline-flex;
}
.progress-ring {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.image {
  width: var(--size);
  height: var(--size);
  rotate: -90deg;
  transform-origin: 50% 50%;
}
.track,
.indicator {
  --radius: calc(var(--size) / 2 - max(var(--track-width), var(--indicator-width)) * 0.5);
  --circumference: calc(var(--radius) * 2 * 3.141592654);
  fill: none;
  r: var(--radius);
  cx: calc(var(--size) / 2);
  cy: calc(var(--size) / 2);
}
.track {
  stroke: var(--track-color);
  stroke-width: var(--track-width);
}
.indicator {
  stroke: var(--indicator-color);
  stroke-width: var(--indicator-width);
  stroke-linecap: round;
  transition-property: stroke-dashoffset;
  transition-duration: var(--indicator-transition-duration);
  stroke-dasharray: var(--circumference) var(--circumference);
  stroke-dashoffset: calc(var(--circumference) - var(--percentage) * var(--circumference));
}
.label {
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  user-select: none;
  -webkit-user-select: none;
}
`))},65686:function(e,t,i){"use strict";i.a(e,(async function(e,a){try{i.d(t,{A:function(){return w}});var r=i(44734),n=i(56038),o=i(69683),s=i(6454),l=i(25460),c=(i(2892),i(96196)),d=i(77845),h=i(32510),p=i(17060),u=i(2355),f=e([p]);p=(f.then?(await f)():f)[0];var v,g=e=>e,_=Object.defineProperty,m=Object.getOwnPropertyDescriptor,y=(e,t,i,a)=>{for(var r,n=a>1?void 0:a?m(t,i):t,o=e.length-1;o>=0;o--)(r=e[o])&&(n=(a?r(t,i,n):r(n))||n);return a&&n&&_(t,i,n),n},w=function(e){function t(){var e;return(0,r.A)(this,t),(e=(0,o.A)(this,t,arguments)).localize=new p.c(e),e.value=0,e.label="",e}return(0,s.A)(t,e),(0,n.A)(t,[{key:"updated",value:function(e){if((0,l.A)(t,"updated",this,3)([e]),e.has("value")){var i=parseFloat(getComputedStyle(this.indicator).getPropertyValue("r")),a=2*Math.PI*i,r=a-this.value/100*a;this.indicatorOffset=`${r}px`}}},{key:"render",value:function(){return(0,c.qy)(v||(v=g`
      <div
        part="base"
        class="progress-ring"
        role="progressbar"
        aria-label=${0}
        aria-describedby="label"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow="${0}"
        style="--percentage: ${0}"
      >
        <svg class="image">
          <circle class="track"></circle>
          <circle class="indicator" style="stroke-dashoffset: ${0}"></circle>
        </svg>

        <slot id="label" part="label" class="label"></slot>
      </div>
    `),this.label.length>0?this.label:this.localize.term("progress"),this.value,this.value/100,this.indicatorOffset)}}])}(h.A);w.css=u.A,y([(0,d.P)(".indicator")],w.prototype,"indicator",2),y([(0,d.wk)()],w.prototype,"indicatorOffset",2),y([(0,d.MZ)({type:Number,reflect:!0})],w.prototype,"value",2),y([(0,d.MZ)()],w.prototype,"label",2),w=y([(0,d.EM)("wa-progress-ring")],w),a()}catch(b){a(b)}}))}}]);
//# sourceMappingURL=7394.bcbe2aeb11987ace.js.map