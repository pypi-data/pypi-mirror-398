"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1850"],{91120:function(e,t,a){var o,r,n,i,l,s,c,u,d,p=a(78261),m=a(61397),h=a(31432),b=a(50264),v=a(44734),y=a(56038),_=a(69683),f=a(6454),g=a(25460),k=(a(28706),a(23792),a(62062),a(18111),a(7588),a(61701),a(5506),a(26099),a(3362),a(23500),a(62953),a(62826)),x=a(96196),$=a(77845),w=a(51757),M=a(92542),A=(a(17963),a(87156),e=>e),Z={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3956"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},j=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null,q=function(e){function t(){var e;(0,v.A)(this,t);for(var a=arguments.length,o=new Array(a),r=0;r<a;r++)o[r]=arguments[r];return(e=(0,_.A)(this,t,[].concat(o))).narrow=!1,e.disabled=!1,e}return(0,f.A)(t,e),(0,y.A)(t,[{key:"getFormProperties",value:function(){return{}}},{key:"focus",value:(a=(0,b.A)((0,m.A)().m((function e(){var t,a,o,r,n;return(0,m.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.n=1,this.updateComplete;case 1:if(t=this.renderRoot.querySelector(".root")){e.n=2;break}return e.a(2);case 2:a=(0,h.A)(t.children),e.p=3,a.s();case 4:if((o=a.n()).done){e.n=7;break}if("HA-ALERT"===(r=o.value).tagName){e.n=6;break}if(!(r instanceof x.mN)){e.n=5;break}return e.n=5,r.updateComplete;case 5:return r.focus(),e.a(3,7);case 6:e.n=4;break;case 7:e.n=9;break;case 8:e.p=8,n=e.v,a.e(n);case 9:return e.p=9,a.f(),e.f(9);case 10:return e.a(2)}}),e,this,[[3,8,9,10]])}))),function(){return a.apply(this,arguments)})},{key:"willUpdate",value:function(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{var t;"selector"in e||null===(t=Z[e.type])||void 0===t||t.call(Z)}))}},{key:"render",value:function(){return(0,x.qy)(o||(o=A`
      <div class="root" part="root">
        ${0}
        ${0}
      </div>
    `),this.error&&this.error.base?(0,x.qy)(r||(r=A`
              <ha-alert alert-type="error">
                ${0}
              </ha-alert>
            `),this._computeError(this.error.base,this.schema)):"",this.schema.map((e=>{var t,a=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),o=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return(0,x.qy)(n||(n=A`
            ${0}
            ${0}
          `),a?(0,x.qy)(i||(i=A`
                  <ha-alert own-margin alert-type="error">
                    ${0}
                  </ha-alert>
                `),this._computeError(a,e)):o?(0,x.qy)(l||(l=A`
                    <ha-alert own-margin alert-type="warning">
                      ${0}
                    </ha-alert>
                  `),this._computeWarning(o,e)):"","selector"in e?(0,x.qy)(s||(s=A`<ha-selector
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
                ></ha-selector>`),e,this.hass,this.narrow,e.name,e.selector,j(this.data,e),this._computeLabel(e,this.data),e.disabled||this.disabled||!1,e.required?void 0:e.default,this._computeHelper(e),this.localizeValue,e.required||!1,this._generateContext(e)):(0,w._)(this.fieldElementName(e.type),Object.assign({schema:e,data:j(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:null===(t=this.hass)||void 0===t?void 0:t.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e)},this.getFormProperties())))})))}},{key:"fieldElementName",value:function(e){return`ha-form-${e}`}},{key:"_generateContext",value:function(e){if(e.context){for(var t={},a=0,o=Object.entries(e.context);a<o.length;a++){var r=(0,p.A)(o[a],2),n=r[0],i=r[1];t[n]=this.data[i]}return t}}},{key:"createRenderRoot",value:function(){var e=(0,g.A)(t,"createRenderRoot",this,3)([]);return this.addValueChangedListener(e),e}},{key:"addValueChangedListener",value:function(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();var t=e.target.schema;if(e.target!==this){var a=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data=Object.assign(Object.assign({},this.data),a),(0,M.r)(this,"value-changed",{value:this.data})}}))}},{key:"_computeLabel",value:function(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}},{key:"_computeHelper",value:function(e){return this.computeHelper?this.computeHelper(e):""}},{key:"_computeError",value:function(e,t){return Array.isArray(e)?(0,x.qy)(c||(c=A`<ul>
        ${0}
      </ul>`),e.map((e=>(0,x.qy)(u||(u=A`<li>
              ${0}
            </li>`),this.computeError?this.computeError(e,t):e)))):this.computeError?this.computeError(e,t):e}},{key:"_computeWarning",value:function(e,t){return this.computeWarning?this.computeWarning(e,t):e}}]);var a}(x.WF);q.shadowRootOptions={mode:"open",delegatesFocus:!0},q.styles=(0,x.AH)(d||(d=A`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `)),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,k.__decorate)([(0,$.MZ)({type:Boolean})],q.prototype,"narrow",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"data",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"schema",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"error",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"warning",void 0),(0,k.__decorate)([(0,$.MZ)({type:Boolean})],q.prototype,"disabled",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"computeError",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"computeWarning",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"computeLabel",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"computeHelper",void 0),(0,k.__decorate)([(0,$.MZ)({attribute:!1})],q.prototype,"localizeValue",void 0),q=(0,k.__decorate)([(0,$.EM)("ha-form")],q)},49100:function(e,t,a){a.r(t),a.d(t,{HaSelectorSelector:function(){return _}});var o,r,n=a(94741),i=a(44734),l=a(56038),s=a(69683),c=a(6454),u=(a(28706),a(62062),a(18111),a(61701),a(26099),a(16034),a(62826)),d=a(96196),p=a(77845),m=a(22786),h=a(92542),b=(a(91120),e=>e),v={number:{min:1,max:100}},y={action:[],area:[{name:"multiple",selector:{boolean:{}}}],attribute:[{name:"entity_id",selector:{entity:{}}}],boolean:[],color_temp:[{name:"unit",selector:{select:{options:["kelvin","mired"]}}},{name:"min",selector:{number:{mode:"box"}}},{name:"max",selector:{number:{mode:"box"}}}],condition:[],date:[],datetime:[],device:[{name:"multiple",selector:{boolean:{}}}],duration:[{name:"enable_day",selector:{boolean:{}}},{name:"enable_millisecond",selector:{boolean:{}}}],entity:[{name:"multiple",selector:{boolean:{}}}],floor:[{name:"multiple",selector:{boolean:{}}}],icon:[],location:[],media:[{name:"accept",selector:{text:{multiple:!0}}}],number:[{name:"min",selector:{number:{mode:"box",step:"any"}}},{name:"max",selector:{number:{mode:"box",step:"any"}}},{name:"step",selector:{number:{mode:"box",step:"any"}}}],object:[],color_rgb:[],select:[{name:"options",selector:{object:{}}},{name:"multiple",selector:{boolean:{}}}],state:[{name:"entity_id",selector:{entity:{}}},{name:"multiple",selector:{boolean:{}}}],target:[],template:[],text:[{name:"multiple",selector:{boolean:{}}},{name:"multiline",selector:{boolean:{}}},{name:"prefix",selector:{text:{}}},{name:"suffix",selector:{text:{}}}],theme:[],time:[]},_=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,o=new Array(a),r=0;r<a;r++)o[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(o))).disabled=!1,e.narrow=!1,e.required=!0,e._yamlMode=!1,e._schema=(0,m.A)(((e,t)=>[{name:"type",required:!0,selector:{select:{mode:"dropdown",options:Object.keys(y).concat("manual").map((e=>({label:t(`ui.components.selectors.selector.types.${e}`)||e,value:e})))}}}].concat((0,n.A)("manual"===e?[{name:"manual",selector:{object:{}}}]:[]),(0,n.A)(y[e]?y[e].length>1?[{name:"",type:"expandable",title:t("ui.components.selectors.selector.options"),schema:y[e]}]:y[e]:[])))),e._computeLabelCallback=t=>e.hass.localize(`ui.components.selectors.selector.${t.name}`)||t.name,e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"shouldUpdate",value:function(e){return 1!==e.size||!e.has("hass")}},{key:"render",value:function(){var e,t;if(this._yamlMode)e={type:t="manual",manual:this.value};else{t=Object.keys(this.value)[0];var a=Object.values(this.value)[0];e=Object.assign({type:t},"object"==typeof a?a:[])}var r=this._schema(t,this.hass.localize);return(0,d.qy)(o||(o=b`<div>
      <p>${0}</p>
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        .computeLabel=${0}
        @value-changed=${0}
        .narrow=${0}
      ></ha-form>
    </div>`),this.label?this.label:"",this.hass,e,r,this._computeLabelCallback,this._valueChanged,this.narrow)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value,a=t.type;if(a&&"object"==typeof t&&0!==Object.keys(t).length){var o,r=Object.keys(this.value)[0];if("manual"===a&&!this._yamlMode)return this._yamlMode=!0,void this.requestUpdate();if("manual"!==a||void 0!==t.manual)"manual"!==a&&(this._yamlMode=!1),delete t.type,o="manual"===a?t.manual:a===r?{[a]:Object.assign({},t.manual?t.manual[r]:t)}:{[a]:Object.assign({},v[a])},(0,h.r)(this,"value-changed",{value:o})}}}])}(d.WF);_.styles=(0,d.AH)(r||(r=b`
    .title {
      font-size: var(--ha-font-size-l);
      padding-top: 16px;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 16px;
      padding-left: 16px;
      padding-right: 4px;
      padding-inline-start: 16px;
      padding-inline-end: 4px;
      white-space: nowrap;
    }
  `)),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],_.prototype,"value",void 0),(0,u.__decorate)([(0,p.MZ)()],_.prototype,"label",void 0),(0,u.__decorate)([(0,p.MZ)()],_.prototype,"helper",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],_.prototype,"disabled",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean})],_.prototype,"narrow",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean,reflect:!0})],_.prototype,"required",void 0),_=(0,u.__decorate)([(0,p.EM)("ha-selector-selector")],_)}}]);
//# sourceMappingURL=1850.34cd65c7e1d15f54.js.map