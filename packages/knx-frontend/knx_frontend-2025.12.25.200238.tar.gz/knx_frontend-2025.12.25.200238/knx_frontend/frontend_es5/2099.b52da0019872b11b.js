"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2099"],{84834:function(t,e,a){a.a(t,(async function(t,i){try{a.d(e,{Yq:function(){return u},zB:function(){return d}});a(50113),a(18111),a(20116),a(26099);var o=a(22),r=a(22786),n=a(81793),s=a(74309),l=t([o,s]);[o,s]=l.then?(await l)():l;(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{weekday:"long",month:"long",day:"numeric",timeZone:(0,s.w)(t.time_zone,e)})));var u=(t,e,a)=>c(e,a.time_zone).format(t),c=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",month:"long",day:"numeric",timeZone:(0,s.w)(t.time_zone,e)}))),d=((0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",month:"short",day:"numeric",timeZone:(0,s.w)(t.time_zone,e)}))),(t,e,a)=>{var i,o,r,s,l=h(e,a.time_zone);if(e.date_format===n.ow.language||e.date_format===n.ow.system)return l.format(t);var u=l.formatToParts(t),c=null===(i=u.find((t=>"literal"===t.type)))||void 0===i?void 0:i.value,d=null===(o=u.find((t=>"day"===t.type)))||void 0===o?void 0:o.value,m=null===(r=u.find((t=>"month"===t.type)))||void 0===r?void 0:r.value,p=null===(s=u.find((t=>"year"===t.type)))||void 0===s?void 0:s.value,v=u[u.length-1],f="literal"===(null==v?void 0:v.type)?null==v?void 0:v.value:"";return"bg"===e.language&&e.date_format===n.ow.YMD&&(f=""),{[n.ow.DMY]:`${d}${c}${m}${c}${p}${f}`,[n.ow.MDY]:`${m}${c}${d}${c}${p}${f}`,[n.ow.YMD]:`${p}${c}${m}${c}${d}${f}`}[e.date_format]}),h=(0,r.A)(((t,e)=>{var a=t.date_format===n.ow.system?void 0:t.language;return t.date_format===n.ow.language||(t.date_format,n.ow.system),new Intl.DateTimeFormat(a,{year:"numeric",month:"numeric",day:"numeric",timeZone:(0,s.w)(t.time_zone,e)})}));(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{day:"numeric",month:"short",timeZone:(0,s.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{month:"long",year:"numeric",timeZone:(0,s.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{month:"long",timeZone:(0,s.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",timeZone:(0,s.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{weekday:"long",timeZone:(0,s.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{weekday:"short",timeZone:(0,s.w)(t.time_zone,e)})));i()}catch(m){i(m)}}))},49284:function(t,e,a){a.a(t,(async function(t,i){try{a.d(e,{r6:function(){return d},yg:function(){return m}});var o=a(22),r=a(22786),n=a(84834),s=a(4359),l=a(74309),u=a(59006),c=t([o,n,s,l]);[o,n,s,l]=c.then?(await c)():c;var d=(t,e,a)=>h(e,a.time_zone).format(t),h=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",month:"long",day:"numeric",hour:(0,u.J)(t)?"numeric":"2-digit",minute:"2-digit",hourCycle:(0,u.J)(t)?"h12":"h23",timeZone:(0,l.w)(t.time_zone,e)}))),m=((0,r.A)((()=>new Intl.DateTimeFormat(void 0,{year:"numeric",month:"long",day:"numeric",hour:"2-digit",minute:"2-digit"}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",month:"short",day:"numeric",hour:(0,u.J)(t)?"numeric":"2-digit",minute:"2-digit",hourCycle:(0,u.J)(t)?"h12":"h23",timeZone:(0,l.w)(t.time_zone,e)}))),(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{month:"short",day:"numeric",hour:(0,u.J)(t)?"numeric":"2-digit",minute:"2-digit",hourCycle:(0,u.J)(t)?"h12":"h23",timeZone:(0,l.w)(t.time_zone,e)}))),(t,e,a)=>p(e,a.time_zone).format(t)),p=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{year:"numeric",month:"long",day:"numeric",hour:(0,u.J)(t)?"numeric":"2-digit",minute:"2-digit",second:"2-digit",hourCycle:(0,u.J)(t)?"h12":"h23",timeZone:(0,l.w)(t.time_zone,e)})));i()}catch(v){i(v)}}))},4359:function(t,e,a){a.a(t,(async function(t,i){try{a.d(e,{LW:function(){return v},Xs:function(){return m},fU:function(){return u},ie:function(){return d}});var o=a(22),r=a(22786),n=a(74309),s=a(59006),l=t([o,n]);[o,n]=l.then?(await l)():l;var u=(t,e,a)=>c(e,a.time_zone).format(t),c=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{hour:"numeric",minute:"2-digit",hourCycle:(0,s.J)(t)?"h12":"h23",timeZone:(0,n.w)(t.time_zone,e)}))),d=(t,e,a)=>h(e,a.time_zone).format(t),h=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{hour:(0,s.J)(t)?"numeric":"2-digit",minute:"2-digit",second:"2-digit",hourCycle:(0,s.J)(t)?"h12":"h23",timeZone:(0,n.w)(t.time_zone,e)}))),m=(t,e,a)=>p(e,a.time_zone).format(t),p=(0,r.A)(((t,e)=>new Intl.DateTimeFormat(t.language,{weekday:"long",hour:(0,s.J)(t)?"numeric":"2-digit",minute:"2-digit",hourCycle:(0,s.J)(t)?"h12":"h23",timeZone:(0,n.w)(t.time_zone,e)}))),v=(t,e,a)=>f(e,a.time_zone).format(t),f=(0,r.A)(((t,e)=>new Intl.DateTimeFormat("en-GB",{hour:"numeric",minute:"2-digit",hour12:!1,timeZone:(0,n.w)(t.time_zone,e)})));i()}catch(y){i(y)}}))},74309:function(t,e,a){a.a(t,(async function(t,i){try{a.d(e,{w:function(){return h}});var o,r,n,s=a(22),l=a(81793),u=t([s]);s=(u.then?(await u)():u)[0];var c=null===(o=Intl.DateTimeFormat)||void 0===o||null===(r=(n=o.call(Intl)).resolvedOptions)||void 0===r?void 0:r.call(n).timeZone,d=null!=c?c:"UTC",h=(t,e)=>t===l.Wj.local&&c?d:e;i()}catch(m){i(m)}}))},59006:function(t,e,a){a.d(e,{J:function(){return r}});a(74423);var i=a(22786),o=a(81793),r=(0,i.A)((t=>{if(t.time_format===o.Hg.language||t.time_format===o.Hg.system){var e=t.time_format===o.Hg.language?t.language:void 0;return new Date("January 1, 2023 22:00:00").toLocaleString(e).includes("10")}return t.time_format===o.Hg.am_pm}))},61003:function(t,e,a){a.d(e,{H:function(){return r}});var i=a(61397),o=a(50264),r=(a(16280),a(23792),a(62062),a(18111),a(61701),a(26099),a(3362),a(62953),function(){var t=(0,o.A)((0,i.A)().m((function t(e){var o,r,s,l,u;return(0,i.A)().w((function(t){for(;;)switch(t.n){case 0:if(e.parentNode){t.n=1;break}throw new Error("Cannot setup Leaflet map on disconnected element");case 1:return t.n=2,Promise.resolve().then(a.t.bind(a,78572,23));case 2:return(o=t.v.default).Icon.Default.imagePath="/static/images/leaflet/images/",t.n=3,a.e("3757").then(a.t.bind(a,17948,23));case 3:return r=o.map(e),(s=document.createElement("link")).setAttribute("href","/static/images/leaflet/leaflet.css"),s.setAttribute("rel","stylesheet"),e.parentNode.appendChild(s),(l=document.createElement("link")).setAttribute("href","/static/images/leaflet/MarkerCluster.css"),l.setAttribute("rel","stylesheet"),e.parentNode.appendChild(l),r.setView([52.3731339,4.8903147],13),u=n(o).addTo(r),t.a(2,[r,o,u])}}),t)})));return function(e){return t.apply(this,arguments)}}()),n=t=>t.tileLayer("https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}"+(t.Browser.retina?"@2x.png":".png"),{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attributions">CARTO</a>',subdomains:"abcd",minZoom:0,maxZoom:20})},35655:function(t,e,a){a.d(e,{q:function(){return u}});var i=a(44734),o=a(56038),r=a(69683),n=a(6454),s=a(25460),l=a(78572),u=function(t){function e(t,a,o){var n;return(0,i.A)(this,e),(n=(0,r.A)(this,e,[t,o])).decorationLayer=a,n}return(0,n.A)(e,t),(0,o.A)(e,[{key:"onAdd",value:function(t){var a;return(0,s.A)(e,"onAdd",this,3)([t]),null===(a=this.decorationLayer)||void 0===a||a.addTo(t),this}},{key:"onRemove",value:function(t){var a;return null===(a=this.decorationLayer)||void 0===a||a.remove(),(0,s.A)(e,"onRemove",this,3)([t])}}])}(l.Marker)},91120:function(t,e,a){var i,o,r,n,s,l,u,c,d,h=a(78261),m=a(61397),p=a(31432),v=a(50264),f=a(44734),y=a(56038),_=a(69683),g=a(6454),b=a(25460),k=(a(28706),a(23792),a(62062),a(18111),a(7588),a(61701),a(5506),a(26099),a(3362),a(23500),a(62953),a(62826)),M=a(96196),w=a(77845),A=a(51757),Z=a(92542),z=(a(17963),a(87156),t=>t),L={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3956"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},$=(t,e)=>t?!e.name||e.flatten?t:t[e.name]:null,C=function(t){function e(){var t;(0,f.A)(this,e);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(t=(0,_.A)(this,e,[].concat(i))).narrow=!1,t.disabled=!1,t}return(0,g.A)(e,t),(0,y.A)(e,[{key:"getFormProperties",value:function(){return{}}},{key:"focus",value:(a=(0,v.A)((0,m.A)().m((function t(){var e,a,i,o,r;return(0,m.A)().w((function(t){for(;;)switch(t.p=t.n){case 0:return t.n=1,this.updateComplete;case 1:if(e=this.renderRoot.querySelector(".root")){t.n=2;break}return t.a(2);case 2:a=(0,p.A)(e.children),t.p=3,a.s();case 4:if((i=a.n()).done){t.n=7;break}if("HA-ALERT"===(o=i.value).tagName){t.n=6;break}if(!(o instanceof M.mN)){t.n=5;break}return t.n=5,o.updateComplete;case 5:return o.focus(),t.a(3,7);case 6:t.n=4;break;case 7:t.n=9;break;case 8:t.p=8,r=t.v,a.e(r);case 9:return t.p=9,a.f(),t.f(9);case 10:return t.a(2)}}),t,this,[[3,8,9,10]])}))),function(){return a.apply(this,arguments)})},{key:"willUpdate",value:function(t){t.has("schema")&&this.schema&&this.schema.forEach((t=>{var e;"selector"in t||null===(e=L[t.type])||void 0===e||e.call(L)}))}},{key:"render",value:function(){return(0,M.qy)(i||(i=z`
      <div class="root" part="root">
        ${0}
        ${0}
      </div>
    `),this.error&&this.error.base?(0,M.qy)(o||(o=z`
              <ha-alert alert-type="error">
                ${0}
              </ha-alert>
            `),this._computeError(this.error.base,this.schema)):"",this.schema.map((t=>{var e,a=((t,e)=>t&&e.name?t[e.name]:null)(this.error,t),i=((t,e)=>t&&e.name?t[e.name]:null)(this.warning,t);return(0,M.qy)(r||(r=z`
            ${0}
            ${0}
          `),a?(0,M.qy)(n||(n=z`
                  <ha-alert own-margin alert-type="error">
                    ${0}
                  </ha-alert>
                `),this._computeError(a,t)):i?(0,M.qy)(s||(s=z`
                    <ha-alert own-margin alert-type="warning">
                      ${0}
                    </ha-alert>
                  `),this._computeWarning(i,t)):"","selector"in t?(0,M.qy)(l||(l=z`<ha-selector
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
                ></ha-selector>`),t,this.hass,this.narrow,t.name,t.selector,$(this.data,t),this._computeLabel(t,this.data),t.disabled||this.disabled||!1,t.required?void 0:t.default,this._computeHelper(t),this.localizeValue,t.required||!1,this._generateContext(t)):(0,A._)(this.fieldElementName(t.type),Object.assign({schema:t,data:$(this.data,t),label:this._computeLabel(t,this.data),helper:this._computeHelper(t),disabled:this.disabled||t.disabled||!1,hass:this.hass,localize:null===(e=this.hass)||void 0===e?void 0:e.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(t)},this.getFormProperties())))})))}},{key:"fieldElementName",value:function(t){return`ha-form-${t}`}},{key:"_generateContext",value:function(t){if(t.context){for(var e={},a=0,i=Object.entries(t.context);a<i.length;a++){var o=(0,h.A)(i[a],2),r=o[0],n=o[1];e[r]=this.data[n]}return e}}},{key:"createRenderRoot",value:function(){var t=(0,b.A)(e,"createRenderRoot",this,3)([]);return this.addValueChangedListener(t),t}},{key:"addValueChangedListener",value:function(t){t.addEventListener("value-changed",(t=>{t.stopPropagation();var e=t.target.schema;if(t.target!==this){var a=!e.name||"flatten"in e&&e.flatten?t.detail.value:{[e.name]:t.detail.value};this.data=Object.assign(Object.assign({},this.data),a),(0,Z.r)(this,"value-changed",{value:this.data})}}))}},{key:"_computeLabel",value:function(t,e){return this.computeLabel?this.computeLabel(t,e):t?t.name:""}},{key:"_computeHelper",value:function(t){return this.computeHelper?this.computeHelper(t):""}},{key:"_computeError",value:function(t,e){return Array.isArray(t)?(0,M.qy)(u||(u=z`<ul>
        ${0}
      </ul>`),t.map((t=>(0,M.qy)(c||(c=z`<li>
              ${0}
            </li>`),this.computeError?this.computeError(t,e):t)))):this.computeError?this.computeError(t,e):t}},{key:"_computeWarning",value:function(t,e){return this.computeWarning?this.computeWarning(t,e):t}}]);var a}(M.WF);C.shadowRootOptions={mode:"open",delegatesFocus:!0},C.styles=(0,M.AH)(d||(d=z`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `)),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"hass",void 0),(0,k.__decorate)([(0,w.MZ)({type:Boolean})],C.prototype,"narrow",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"data",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"schema",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"error",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"warning",void 0),(0,k.__decorate)([(0,w.MZ)({type:Boolean})],C.prototype,"disabled",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"computeError",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"computeWarning",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"computeLabel",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"computeHelper",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],C.prototype,"localizeValue",void 0),C=(0,k.__decorate)([(0,w.EM)("ha-form")],C)},74686:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{HaLocationSelector:function(){return k}});var o=a(78261),r=a(94741),n=a(44734),s=a(56038),l=a(75864),u=a(69683),c=a(6454),d=(a(28706),a(62826)),h=a(96196),m=a(77845),p=a(22786),v=a(92542),f=a(77550),y=(a(91120),t([f]));f=(y.then?(await y)():y)[0];var _,g,b=t=>t,k=function(t){function e(){var t;(0,n.A)(this,e);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(t=(0,u.A)(this,e,[].concat(i))).disabled=!1,t._schema=(0,p.A)(((t,e,a)=>[{name:"",type:"grid",schema:[{name:"latitude",required:!0,selector:{number:{step:"any",unit_of_measurement:"°"}}},{name:"longitude",required:!0,selector:{number:{step:"any",unit_of_measurement:"°"}}}]}].concat((0,r.A)(e?[{name:"radius",required:!0,default:1e3,disabled:!!a,selector:{number:{min:0,step:1,mode:"box",unit_of_measurement:t("ui.components.selectors.location.radius_meters")}}}]:[])))),t._location=(0,p.A)(((e,a)=>{var i,o,r,n,s,u,c=getComputedStyle((0,l.A)(t)),d=null!==(i=e.location)&&void 0!==i&&i.radius?c.getPropertyValue("--zone-radius-color")||c.getPropertyValue("--accent-color"):void 0;return[{id:"location",latitude:!a||isNaN(a.latitude)?t.hass.config.latitude:a.latitude,longitude:!a||isNaN(a.longitude)?t.hass.config.longitude:a.longitude,radius:null!==(o=e.location)&&void 0!==o&&o.radius?(null==a?void 0:a.radius)||1e3:void 0,radius_color:d,icon:null!==(r=e.location)&&void 0!==r&&r.icon||null!==(n=e.location)&&void 0!==n&&n.radius?"mdi:map-marker-radius":"mdi:map-marker",location_editable:!0,radius_editable:!(null===(s=e.location)||void 0===s||!s.radius||null!==(u=e.location)&&void 0!==u&&u.radius_readonly)}]})),t._computeLabel=e=>e.name?t.hass.localize(`ui.components.selectors.location.${e.name}`):"",t}return(0,c.A)(e,t),(0,s.A)(e,[{key:"willUpdate",value:function(){var t;this.value||(this.value={latitude:this.hass.config.latitude,longitude:this.hass.config.longitude,radius:null!==(t=this.selector.location)&&void 0!==t&&t.radius?1e3:void 0})}},{key:"render",value:function(){var t,e;return(0,h.qy)(_||(_=b`
      <p>${0}</p>
      <ha-locations-editor
        class="flex"
        .hass=${0}
        .helper=${0}
        .locations=${0}
        @location-updated=${0}
        @radius-updated=${0}
        pin-on-click
      ></ha-locations-editor>
      <ha-form
        .hass=${0}
        .schema=${0}
        .data=${0}
        .computeLabel=${0}
        .disabled=${0}
        @value-changed=${0}
      ></ha-form>
    `),this.label?this.label:"",this.hass,this.helper,this._location(this.selector,this.value),this._locationChanged,this._radiusChanged,this.hass,this._schema(this.hass.localize,null===(t=this.selector.location)||void 0===t?void 0:t.radius,null===(e=this.selector.location)||void 0===e?void 0:e.radius_readonly),this.value,this._computeLabel,this.disabled,this._valueChanged)}},{key:"_locationChanged",value:function(t){var e=(0,o.A)(t.detail.location,2),a=e[0],i=e[1];(0,v.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.value),{},{latitude:a,longitude:i})})}},{key:"_radiusChanged",value:function(t){var e=Math.round(t.detail.radius);(0,v.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.value),{},{radius:e})})}},{key:"_valueChanged",value:function(t){var e,a;t.stopPropagation();var i=t.detail.value,o=Math.round(t.detail.value.radius);(0,v.r)(this,"value-changed",{value:Object.assign({latitude:i.latitude,longitude:i.longitude},null===(e=this.selector.location)||void 0===e||!e.radius||null!==(a=this.selector.location)&&void 0!==a&&a.radius_readonly?{}:{radius:o})})}}])}(h.WF);k.styles=(0,h.AH)(g||(g=b`
    ha-locations-editor {
      display: block;
      height: 400px;
      margin-bottom: 16px;
    }
    p {
      margin-top: 0;
    }
  `)),(0,d.__decorate)([(0,m.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,d.__decorate)([(0,m.MZ)({attribute:!1})],k.prototype,"selector",void 0),(0,d.__decorate)([(0,m.MZ)({type:Object})],k.prototype,"value",void 0),(0,d.__decorate)([(0,m.MZ)()],k.prototype,"label",void 0),(0,d.__decorate)([(0,m.MZ)()],k.prototype,"helper",void 0),(0,d.__decorate)([(0,m.MZ)({type:Boolean,reflect:!0})],k.prototype,"disabled",void 0),k=(0,d.__decorate)([(0,m.EM)("ha-selector-location")],k),i()}catch(M){i(M)}}))},4148:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(44734),o=a(56038),r=a(69683),n=a(6454),s=a(62826),l=a(96196),u=a(77845),c=a(45847),d=a(97382),h=a(43197),m=(a(22598),a(60961),t([h]));h=(m.then?(await m)():m)[0];var p,v,f,y,_=t=>t,g=function(t){function e(){return(0,i.A)(this,e),(0,r.A)(this,e,arguments)}return(0,n.A)(e,t),(0,o.A)(e,[{key:"render",value:function(){var t,e,a=this.icon||this.stateObj&&(null===(t=this.hass)||void 0===t||null===(t=t.entities[this.stateObj.entity_id])||void 0===t?void 0:t.icon)||(null===(e=this.stateObj)||void 0===e?void 0:e.attributes.icon);if(a)return(0,l.qy)(p||(p=_`<ha-icon .icon=${0}></ha-icon>`),a);if(!this.stateObj)return l.s6;if(!this.hass)return this._renderFallback();var i=(0,h.fq)(this.hass,this.stateObj,this.stateValue).then((t=>t?(0,l.qy)(v||(v=_`<ha-icon .icon=${0}></ha-icon>`),t):this._renderFallback()));return(0,l.qy)(f||(f=_`${0}`),(0,c.T)(i))}},{key:"_renderFallback",value:function(){var t=(0,d.t)(this.stateObj);return(0,l.qy)(y||(y=_`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),h.l[t]||h.lW)}}])}(l.WF);(0,s.__decorate)([(0,u.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],g.prototype,"stateObj",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],g.prototype,"stateValue",void 0),(0,s.__decorate)([(0,u.MZ)()],g.prototype,"icon",void 0),g=(0,s.__decorate)([(0,u.EM)("ha-state-icon")],g),e()}catch(b){e(b)}}))},41870:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(44734),o=a(56038),r=a(69683),n=a(6454),s=(a(28706),a(62826)),l=a(96196),u=a(77845),c=a(29485),d=a(92542),h=a(4148),m=t([h]);h=(m.then?(await m)():m)[0];var p,v,f,y,_,g=t=>t,b=function(t){function e(){var t;(0,i.A)(this,e);for(var a=arguments.length,o=new Array(a),n=0;n<a;n++)o[n]=arguments[n];return(t=(0,r.A)(this,e,[].concat(o))).showIcon=!1,t}return(0,n.A)(e,t),(0,o.A)(e,[{key:"render",value:function(){var t;return(0,l.qy)(p||(p=g`
      <div
        class="marker ${0}"
        style=${0}
        @click=${0}
      >
        ${0}
      </div>
    `),this.entityPicture?"picture":"",(0,c.W)({"border-color":this.entityColor}),this._badgeTap,this.entityPicture?(0,l.qy)(v||(v=g`<div
              class="entity-picture"
              style=${0}
            ></div>`),(0,c.W)({"background-image":`url(${this.entityPicture})`})):this.showIcon&&this.entityId?(0,l.qy)(f||(f=g`<ha-state-icon
                .hass=${0}
                .stateObj=${0}
              ></ha-state-icon>`),this.hass,null===(t=this.hass)||void 0===t?void 0:t.states[this.entityId]):this.entityUnit?(0,l.qy)(y||(y=g`
                  ${0}
                  <span
                    class="unit"
                    style="display: ${0}"
                    >${0}</span
                  >
                `),this.entityName,this.entityUnit?"initial":"none",this.entityUnit):this.entityName)}},{key:"_badgeTap",value:function(t){t.stopPropagation(),this.entityId&&(0,d.r)(this,"hass-more-info",{entityId:this.entityId})}}])}(l.WF);b.styles=(0,l.AH)(_||(_=g`
    .marker {
      display: flex;
      justify-content: center;
      text-align: center;
      align-items: center;
      box-sizing: border-box;
      width: 48px;
      height: 48px;
      font-size: var(--ha-marker-font-size, var(--ha-font-size-xl));
      border-radius: var(--ha-marker-border-radius, 50%);
      border: 1px solid var(--ha-marker-color, var(--primary-color));
      color: var(--primary-text-color);
      background-color: var(--card-background-color);
    }
    .marker.picture {
      overflow: hidden;
    }
    .entity-picture {
      background-size: cover;
      height: 100%;
      width: 100%;
    }
    .unit {
      margin-left: 2px;
    }
  `)),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"entity-id",reflect:!0})],b.prototype,"entityId",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"entity-name"})],b.prototype,"entityName",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"entity-unit"})],b.prototype,"entityUnit",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"entity-picture"})],b.prototype,"entityPicture",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"entity-color"})],b.prototype,"entityColor",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:"show-icon",type:Boolean})],b.prototype,"showIcon",void 0),customElements.define("ha-entity-marker",b),e()}catch(k){e(k)}}))},77550:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(61397),o=a(50264),r=a(44734),n=a(56038),s=a(69683),l=a(6454),u=a(25460),c=(a(2008),a(23792),a(62062),a(44114),a(18111),a(22489),a(7588),a(61701),a(2892),a(26099),a(16034),a(3362),a(23500),a(62953),a(62826)),d=a(96196),h=a(77845),m=a(22786),p=a(92542),v=(a(56768),a(78888)),f=t([v]);v=(f.then?(await f)():f)[0];var y,_,g,b=t=>t,k=function(t){function e(){var t;return(0,r.A)(this,e),(t=(0,s.A)(this,e)).autoFit=!1,t.zoom=16,t.themeMode="auto",t.pinOnClick=!1,t._circles={},t._getLayers=(0,m.A)(((t,e)=>{var a=[];return Array.prototype.push.apply(a,Object.values(t)),e&&Array.prototype.push.apply(a,Object.values(e)),a})),t._loadPromise=Promise.resolve().then(a.t.bind(a,78572,23)).then((e=>a.e("9293").then(a.t.bind(a,60108,23)).then((()=>(t.Leaflet=e.default,t._updateMarkers(),t.updateComplete.then((()=>t.fitMap()))))))),t}return(0,l.A)(e,t),(0,n.A)(e,[{key:"fitMap",value:function(t){this.map.fitMap(t)}},{key:"fitBounds",value:function(t,e){this.map.fitBounds(t,e)}},{key:"fitMarker",value:(c=(0,o.A)((0,i.A)().m((function t(e,a){var o,r;return(0,i.A)().w((function(t){for(;;)switch(t.n){case 0:if(this.Leaflet){t.n=1;break}return t.n=1,this._loadPromise;case 1:if(this.map.leafletMap&&this._locationMarkers){t.n=2;break}return t.a(2);case 2:if(o=this._locationMarkers[e]){t.n=3;break}return t.a(2);case 3:"getBounds"in o?(this.map.leafletMap.fitBounds(o.getBounds()),o.bringToFront()):(r=this._circles[e])?this.map.leafletMap.fitBounds(r.getBounds()):this.map.leafletMap.setView(o.getLatLng(),(null==a?void 0:a.zoom)||this.zoom);case 4:return t.a(2)}}),t,this)}))),function(t,e){return c.apply(this,arguments)})},{key:"render",value:function(){return(0,d.qy)(y||(y=b`
      <ha-map
        .hass=${0}
        .layers=${0}
        .zoom=${0}
        .autoFit=${0}
        .themeMode=${0}
        .clickable=${0}
        @map-clicked=${0}
      ></ha-map>
      ${0}
    `),this.hass,this._getLayers(this._circles,this._locationMarkers),this.zoom,this.autoFit,this.themeMode,this.pinOnClick,this._mapClicked,this.helper?(0,d.qy)(_||(_=b`<ha-input-helper-text>${0}</ha-input-helper-text>`),this.helper):"")}},{key:"willUpdate",value:function(t){(0,u.A)(e,"willUpdate",this,3)([t]),this.Leaflet&&t.has("locations")&&this._updateMarkers()}},{key:"updated",value:function(t){if(this.Leaflet&&t.has("locations")){var e,a,i=t.get("locations"),o=null===(e=this.locations)||void 0===e?void 0:e.filter(((t,e)=>{var a,o;return!i[e]||(t.latitude!==i[e].latitude||t.longitude!==i[e].longitude)&&(null===(a=this.map.leafletMap)||void 0===a?void 0:a.getBounds().contains({lat:i[e].latitude,lng:i[e].longitude}))&&!(null!==(o=this.map.leafletMap)&&void 0!==o&&o.getBounds().contains({lat:t.latitude,lng:t.longitude}))}));if(1===(null==o?void 0:o.length))null===(a=this.map.leafletMap)||void 0===a||a.panTo({lat:o[0].latitude,lng:o[0].longitude})}}},{key:"_normalizeLongitude",value:function(t){return Math.abs(t)>180?(t%360+540)%360-180:t}},{key:"_updateLocation",value:function(t){var e=t.target,a=e.getLatLng(),i=[a.lat,this._normalizeLongitude(a.lng)];(0,p.r)(this,"location-updated",{id:e.id,location:i},{bubbles:!1})}},{key:"_updateRadius",value:function(t){var e=t.target,a=this._locationMarkers[e.id];(0,p.r)(this,"radius-updated",{id:e.id,radius:a.getRadius()},{bubbles:!1})}},{key:"_markerClicked",value:function(t){var e=t.target;(0,p.r)(this,"marker-clicked",{id:e.id},{bubbles:!1})}},{key:"_mapClicked",value:function(t){if(this.pinOnClick&&this._locationMarkers){var e,a=Object.keys(this._locationMarkers)[0],i=[t.detail.location[0],this._normalizeLongitude(t.detail.location[1])];if((0,p.r)(this,"location-updated",{id:a,location:i},{bubbles:!1}),i[1]!==t.detail.location[1])null===(e=this.map.leafletMap)||void 0===e||e.panTo({lat:i[0],lng:i[1]})}}},{key:"_updateMarkers",value:function(){if(!this.locations||!this.locations.length)return this._circles={},void(this._locationMarkers=void 0);var t={},e={},a=getComputedStyle(this).getPropertyValue("--accent-color");this.locations.forEach((i=>{var o;if(i.icon||i.iconPath){var r,n=document.createElement("div");n.className="named-icon",void 0!==i.name&&(n.innerText=i.name),i.icon?(r=document.createElement("ha-icon")).setAttribute("icon",i.icon):(r=document.createElement("ha-svg-icon")).setAttribute("path",i.iconPath),n.prepend(r),o=this.Leaflet.divIcon({html:n.outerHTML,iconSize:[24,24],className:"light"})}if(i.radius){var s=this.Leaflet.circle([i.latitude,i.longitude],{color:i.radius_color||a,radius:i.radius});i.radius_editable||i.location_editable?(s.editing.enable(),s.addEventListener("add",(()=>{var t=s.editing._moveMarker,e=s.editing._resizeMarkers[0];o&&t.setIcon(o),e.id=t.id=i.id,t.addEventListener("dragend",(t=>this._updateLocation(t))).addEventListener("click",(t=>this._markerClicked(t))),i.radius_editable?e.addEventListener("dragend",(t=>this._updateRadius(t))):e.remove()})),t[i.id]=s):e[i.id]=s}if(!i.radius||!i.radius_editable&&!i.location_editable){var l={title:i.name,draggable:i.location_editable};o&&(l.icon=o);var u=this.Leaflet.marker([i.latitude,i.longitude],l).addEventListener("dragend",(t=>this._updateLocation(t))).addEventListener("click",(t=>this._markerClicked(t)));u.id=i.id,t[i.id]=u}})),this._circles=e,this._locationMarkers=t,(0,p.r)(this,"markers-updated")}}]);var c}(d.WF);k.styles=(0,d.AH)(g||(g=b`
    ha-map {
      display: block;
      height: 100%;
    }
  `)),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],k.prototype,"locations",void 0),(0,c.__decorate)([(0,h.MZ)()],k.prototype,"helper",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:"auto-fit",type:Boolean})],k.prototype,"autoFit",void 0),(0,c.__decorate)([(0,h.MZ)({type:Number})],k.prototype,"zoom",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:"theme-mode",type:String})],k.prototype,"themeMode",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"pin-on-click"})],k.prototype,"pinOnClick",void 0),(0,c.__decorate)([(0,h.wk)()],k.prototype,"_locationMarkers",void 0),(0,c.__decorate)([(0,h.wk)()],k.prototype,"_circles",void 0),(0,c.__decorate)([(0,h.P)("ha-map",!0)],k.prototype,"map",void 0),k=(0,c.__decorate)([(0,h.EM)("ha-locations-editor")],k),e()}catch(M){e(M)}}))},78888:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(78261),o=a(31432),r=a(61397),n=a(50264),s=a(44734),l=a(56038),u=a(69683),c=a(6454),d=a(25460),h=a(71950),m=(a(28706),a(62062),a(44114),a(18111),a(7588),a(61701),a(2892),a(26099),a(23500),a(62826)),p=a(34909),v=a(96196),f=a(77845),y=a(49284),_=a(4359),g=a(92542),b=a(61003),k=a(97382),M=a(91889),w=a(35655),A=a(80111),Z=(a(60733),a(41870)),z=t([h,Z,y,_]);[h,Z,y,_]=z.then?(await z)():z;var L,$=250,C=t=>"string"==typeof t?t:t.entity_id,F=function(t){function e(){var t;(0,s.A)(this,e);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(t=(0,u.A)(this,e,[].concat(i))).clickable=!1,t.autoFit=!1,t.renderPassive=!1,t.interactiveZones=!1,t.fitZones=!1,t.themeMode="auto",t.zoom=14,t.clusterMarkers=!0,t._loaded=!1,t._mapItems=[],t._mapFocusItems=[],t._mapZones=[],t._mapFocusZones=[],t._mapPaths=[],t._clickCount=0,t._isProgrammaticFit=!1,t._pauseAutoFit=!1,t._handleVisibilityChange=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:document.hidden||setTimeout((()=>{t._pauseAutoFit=!1}),500);case 1:return e.a(2)}}),e)}))),t._loading=!1,t}return(0,c.A)(e,t),(0,l.A)(e,[{key:"connectedCallback",value:function(){this._pauseAutoFit=!1,document.addEventListener("visibilitychange",this._handleVisibilityChange),this._handleVisibilityChange(),(0,d.A)(e,"connectedCallback",this,3)([]),this._loadMap(),this._attachObserver()}},{key:"disconnectedCallback",value:function(){(0,d.A)(e,"disconnectedCallback",this,3)([]),document.removeEventListener("visibilitychange",this._handleVisibilityChange),this.leafletMap&&(this.leafletMap.remove(),this.leafletMap=void 0,this.Leaflet=void 0),this._loaded=!1,this._resizeObserver&&this._resizeObserver.unobserve(this)}},{key:"update",value:function(t){var a,i;if((0,d.A)(e,"update",this,3)([t]),this._loaded){var r=!1,n=t.get("hass");if(t.has("_loaded")||t.has("entities"))this._drawEntities(),r=!this._pauseAutoFit;else if(this._loaded&&n&&this.entities){var s,l=(0,o.A)(this.entities);try{for(l.s();!(s=l.n()).done;){var u=s.value;if(n.states[C(u)]!==this.hass.states[C(u)]){this._drawEntities(),r=!this._pauseAutoFit;break}}}catch(c){l.e(c)}finally{l.f()}}t.has("clusterMarkers")&&this._drawEntities(),(t.has("_loaded")||t.has("paths"))&&this._drawPaths(),(t.has("_loaded")||t.has("layers"))&&(this._drawLayers(t.get("layers")),r=!0),(t.has("_loaded")||this.autoFit&&r)&&this.fitMap(),t.has("zoom")&&(this._isProgrammaticFit=!0,this.leafletMap.setZoom(this.zoom),setTimeout((()=>{this._isProgrammaticFit=!1}),$)),(t.has("themeMode")||t.has("hass")&&(!n||(null===(a=n.themes)||void 0===a?void 0:a.darkMode)!==(null===(i=this.hass.themes)||void 0===i?void 0:i.darkMode)))&&this._updateMapStyle()}}},{key:"_darkMode",get:function(){return"dark"===this.themeMode||"auto"===this.themeMode&&Boolean(this.hass.themes.darkMode)}},{key:"_updateMapStyle",value:function(){var t=this.renderRoot.querySelector("#map");t.classList.toggle("clickable",this.clickable),t.classList.toggle("dark",this._darkMode),t.classList.toggle("forced-dark","dark"===this.themeMode),t.classList.toggle("forced-light","light"===this.themeMode)}},{key:"_loadMap",value:(h=(0,n.A)((0,r.A)().m((function t(){var e,a,o;return(0,r.A)().w((function(t){for(;;)switch(t.p=t.n){case 0:if(!this._loading){t.n=1;break}return t.a(2);case 1:return(e=this.shadowRoot.getElementById("map"))||((e=document.createElement("div")).id="map",this.shadowRoot.append(e)),this._loading=!0,t.p=2,t.n=3,(0,b.H)(e);case 3:a=t.v,o=(0,i.A)(a,2),this.leafletMap=o[0],this.Leaflet=o[1],this._updateMapStyle(),this.leafletMap.on("click",(t=>{0===this._clickCount&&setTimeout((()=>{1===this._clickCount&&(0,g.r)(this,"map-clicked",{location:[t.latlng.lat,t.latlng.lng]}),this._clickCount=0}),250),this._clickCount++})),this.leafletMap.on("zoomstart",(()=>{this._isProgrammaticFit||(this._pauseAutoFit=!0)})),this.leafletMap.on("movestart",(()=>{this._isProgrammaticFit||(this._pauseAutoFit=!0)})),this._loaded=!0;case 4:return t.p=4,this._loading=!1,t.f(4);case 5:return t.a(2)}}),t,this,[[2,,4,5]])}))),function(){return h.apply(this,arguments)})},{key:"fitMap",value:function(t){var e,a,i,o;if(null!=t&&t.unpause_autofit&&(this._pauseAutoFit=!1),this.leafletMap&&this.Leaflet&&this.hass){if(!(this._mapFocusItems.length||this._mapFocusZones.length||null!==(e=this.layers)&&void 0!==e&&e.length))return this._isProgrammaticFit=!0,this.leafletMap.setView(new this.Leaflet.LatLng(this.hass.config.latitude,this.hass.config.longitude),(null==t?void 0:t.zoom)||this.zoom),void setTimeout((()=>{this._isProgrammaticFit=!1}),$);var r=this.Leaflet.latLngBounds(this._mapFocusItems?this._mapFocusItems.map((t=>t.getLatLng())):[]);null===(a=this._mapFocusZones)||void 0===a||a.forEach((t=>{r.extend("getBounds"in t?t.getBounds():t.getLatLng())})),null===(i=this.layers)||void 0===i||i.forEach((t=>{r.extend("getBounds"in t?t.getBounds():t.getLatLng())})),r=r.pad(null!==(o=null==t?void 0:t.pad)&&void 0!==o?o:.5),this._isProgrammaticFit=!0,this.leafletMap.fitBounds(r,{maxZoom:(null==t?void 0:t.zoom)||this.zoom}),setTimeout((()=>{this._isProgrammaticFit=!1}),$)}}},{key:"fitBounds",value:function(t,e){var a;if(this.leafletMap&&this.Leaflet&&this.hass){var i=this.Leaflet.latLngBounds(t).pad(null!==(a=null==e?void 0:e.pad)&&void 0!==a?a:.5);this._isProgrammaticFit=!0,this.leafletMap.fitBounds(i,{maxZoom:(null==e?void 0:e.zoom)||this.zoom}),setTimeout((()=>{this._isProgrammaticFit=!1}),$)}}},{key:"_drawLayers",value:function(t){if(t&&t.forEach((t=>t.remove())),this.layers){var e=this.leafletMap;this.layers.forEach((t=>{e.addLayer(t)}))}}},{key:"_computePathTooltip",value:function(t,e){var a;return a=t.fullDatetime?(0,y.r6)(e.timestamp,this.hass.locale,this.hass.config):(0,p.c)(e.timestamp)?(0,_.ie)(e.timestamp,this.hass.locale,this.hass.config):(0,_.Xs)(e.timestamp,this.hass.locale,this.hass.config),`${t.name}<br>${a}`}},{key:"_drawPaths",value:function(){var t=this.hass,e=this.leafletMap,a=this.Leaflet;if(t&&e&&a&&(this._mapPaths.length&&(this._mapPaths.forEach((t=>t.remove())),this._mapPaths=[]),this.paths)){var i=getComputedStyle(this).getPropertyValue("--dark-primary-color");this.paths.forEach((t=>{var o,r;t.gradualOpacity&&(o=t.gradualOpacity/(t.points.length-2),r=1-t.gradualOpacity);for(var n=0;n<t.points.length-1;n++){var s=t.gradualOpacity?r+n*o:void 0;this._mapPaths.push(a.circleMarker(t.points[n].point,{radius:A.C?8:3,color:t.color||i,opacity:s,fillOpacity:s,interactive:!0}).bindTooltip(this._computePathTooltip(t,t.points[n]),{direction:"top"})),this._mapPaths.push(a.polyline([t.points[n].point,t.points[n+1].point],{color:t.color||i,opacity:s,interactive:!1}))}var l=t.points.length-1;if(l>=0){var u=t.gradualOpacity?r+l*o:void 0;this._mapPaths.push(a.circleMarker(t.points[l].point,{radius:A.C?8:3,color:t.color||i,opacity:u,fillOpacity:u,interactive:!0}).bindTooltip(this._computePathTooltip(t,t.points[l]),{direction:"top"}))}this._mapPaths.forEach((t=>e.addLayer(t)))}))}}},{key:"_drawEntities",value:function(){var t=this.hass,e=this.leafletMap,a=this.Leaflet;if(t&&e&&a&&(this._mapItems.length&&(this._mapItems.forEach((t=>t.remove())),this._mapItems=[],this._mapFocusItems=[]),this._mapZones.length&&(this._mapZones.forEach((t=>t.remove())),this._mapZones=[],this._mapFocusZones=[]),this._mapCluster&&(this._mapCluster.remove(),this._mapCluster=void 0),this.entities)){var i,r=getComputedStyle(this),n=r.getPropertyValue("--accent-color"),s=r.getPropertyValue("--secondary-text-color"),l=r.getPropertyValue("--dark-primary-color"),u=this._darkMode?"dark":"light",c=(0,o.A)(this.entities);try{for(c.s();!(i=c.n()).done;){var d=i.value,h=t.states[C(d)];if(h){var m="string"!=typeof d?d.name:void 0,p=null!=m?m:(0,M.u)(h),v=h.attributes,f=v.latitude,y=v.longitude,_=v.passive,g=v.icon,b=v.radius,A=v.entity_picture,Z=v.gps_accuracy;if(f&&y)if("zone"!==(0,k.t)(h)){var z="string"!=typeof d&&"state"===d.label_mode?this.hass.formatEntityState(h):"string"!=typeof d&&"attribute"===d.label_mode&&void 0!==d.attribute?this.hass.formatEntityAttributeValue(h,d.attribute):null!=m?m:p.split(" ").map((t=>t[0])).join("").substr(0,3),L=document.createElement("ha-entity-marker");L.hass=this.hass,L.showIcon="string"!=typeof d&&"icon"===d.label_mode,L.entityId=C(d),L.entityName=z,L.entityUnit="string"!=typeof d&&d.unit&&"attribute"===d.label_mode?d.unit:"",L.entityPicture=!A||"string"!=typeof d&&d.label_mode?"":this.hass.hassUrl(A),"string"!=typeof d&&(L.entityColor=d.color);var $=new w.q([f,y],void 0,{icon:a.divIcon({html:L,iconSize:[48,48],className:""}),title:p});"string"!=typeof d&&!1===d.focus||this._mapFocusItems.push($),Z&&($.decorationLayer=a.circle([f,y],{interactive:!1,color:l,radius:Z})),this._mapItems.push($)}else{if(_&&!this.renderPassive)continue;var F="";if(g){var x=document.createElement("ha-icon");x.setAttribute("icon",g),F=x.outerHTML}else{var E=document.createElement("span");E.innerHTML=p,F=E.outerHTML}var P=a.circle([f,y],{interactive:!1,color:_?s:n,radius:b}),I=new w.q([f,y],P,{icon:a.divIcon({html:F,iconSize:[24,24],className:u}),interactive:this.interactiveZones,title:p});this._mapZones.push(I),!this.fitZones||"string"!=typeof d&&!1===d.focus||this._mapFocusZones.push(P)}}}}catch(T){c.e(T)}finally{c.f()}this.clusterMarkers?(this._mapCluster=a.markerClusterGroup({showCoverageOnHover:!1,removeOutsideVisibleBounds:!1,maxClusterRadius:40}),this._mapCluster.addLayers(this._mapItems),e.addLayer(this._mapCluster)):this._mapItems.forEach((t=>e.addLayer(t))),this._mapZones.forEach((t=>e.addLayer(t)))}}},{key:"_attachObserver",value:(a=(0,n.A)((0,r.A)().m((function t(){return(0,r.A)().w((function(t){for(;;)switch(t.n){case 0:this._resizeObserver||(this._resizeObserver=new ResizeObserver((()=>{var t;null===(t=this.leafletMap)||void 0===t||t.invalidateSize({debounceMoveend:!0})}))),this._resizeObserver.observe(this);case 1:return t.a(2)}}),t,this)}))),function(){return a.apply(this,arguments)})}]);var a,h}(v.mN);F.styles=(0,v.AH)(L||(L=(t=>t)`
    :host {
      display: block;
      height: 300px;
    }
    #map {
      height: 100%;
    }
    #map.clickable {
      cursor: pointer;
    }
    #map.dark {
      background: #090909;
    }
    #map.forced-dark {
      color: #ffffff;
      --map-filter: invert(0.9) hue-rotate(170deg) brightness(1.5) contrast(1.2)
        saturate(0.3);
    }
    #map.forced-light {
      background: #ffffff;
      color: #000000;
      --map-filter: invert(0);
    }
    #map.clickable:active,
    #map:active {
      cursor: grabbing;
      cursor: -moz-grabbing;
      cursor: -webkit-grabbing;
    }
    .leaflet-tile-pane {
      filter: var(--map-filter);
    }
    .dark .leaflet-bar a {
      background-color: #1c1c1c;
      color: #ffffff;
    }
    .dark .leaflet-bar a:hover {
      background-color: #313131;
    }
    .leaflet-marker-draggable {
      cursor: move !important;
    }
    .leaflet-edit-resize {
      border-radius: var(--ha-border-radius-circle);
      cursor: nesw-resize !important;
    }
    .named-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      text-align: center;
      color: var(--primary-text-color);
    }
    .leaflet-pane {
      z-index: 0 !important;
    }
    .leaflet-control,
    .leaflet-top,
    .leaflet-bottom {
      z-index: 1 !important;
    }
    .leaflet-tooltip {
      padding: 8px;
      font-size: var(--ha-font-size-s);
      background: rgba(80, 80, 80, 0.9) !important;
      color: white !important;
      border-radius: var(--ha-border-radius-sm);
      box-shadow: none !important;
      text-align: center;
    }

    .marker-cluster div {
      background-clip: padding-box;
      background-color: var(--primary-color);
      border: 3px solid rgba(var(--rgb-primary-color), 0.2);
      width: 32px;
      height: 32px;
      border-radius: var(--ha-border-radius-2xl);
      text-align: center;
      color: var(--text-primary-color);
      font-size: var(--ha-font-size-m);
    }

    .marker-cluster span {
      line-height: var(--ha-line-height-expanded);
    }
  `)),(0,m.__decorate)([(0,f.MZ)({attribute:!1})],F.prototype,"hass",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:!1})],F.prototype,"entities",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:!1})],F.prototype,"paths",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:!1})],F.prototype,"layers",void 0),(0,m.__decorate)([(0,f.MZ)({type:Boolean})],F.prototype,"clickable",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"auto-fit",type:Boolean})],F.prototype,"autoFit",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"render-passive",type:Boolean})],F.prototype,"renderPassive",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"interactive-zones",type:Boolean})],F.prototype,"interactiveZones",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"fit-zones",type:Boolean})],F.prototype,"fitZones",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"theme-mode",type:String})],F.prototype,"themeMode",void 0),(0,m.__decorate)([(0,f.MZ)({type:Number})],F.prototype,"zoom",void 0),(0,m.__decorate)([(0,f.MZ)({attribute:"cluster-markers",type:Boolean})],F.prototype,"clusterMarkers",void 0),(0,m.__decorate)([(0,f.wk)()],F.prototype,"_loaded",void 0),F=(0,m.__decorate)([(0,f.EM)("ha-map")],F),e()}catch(x){e(x)}}))},80111:function(t,e,a){a.d(e,{C:function(){return i}});var i="ontouchstart"in window||navigator.maxTouchPoints>0||navigator.msMaxTouchPoints>0}}]);
//# sourceMappingURL=2099.b52da0019872b11b.js.map