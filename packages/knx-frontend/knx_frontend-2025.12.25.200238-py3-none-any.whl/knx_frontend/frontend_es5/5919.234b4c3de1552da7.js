"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5919"],{91120:function(e,t,a){var r,o,i,n,s,l,c,u,h,d=a(78261),p=a(61397),m=a(31432),_=a(50264),v=a(44734),b=a(56038),y=a(69683),f=a(6454),g=a(25460),k=(a(28706),a(23792),a(62062),a(18111),a(7588),a(61701),a(5506),a(26099),a(3362),a(23500),a(62953),a(62826)),$=a(96196),A=a(77845),w=a(51757),E=a(92542),M=(a(17963),a(87156),e=>e),x={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3956"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},L=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null,q=function(e){function t(){var e;(0,v.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,y.A)(this,t,[].concat(r))).narrow=!1,e.disabled=!1,e}return(0,f.A)(t,e),(0,b.A)(t,[{key:"getFormProperties",value:function(){return{}}},{key:"focus",value:(a=(0,_.A)((0,p.A)().m((function e(){var t,a,r,o,i;return(0,p.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.n=1,this.updateComplete;case 1:if(t=this.renderRoot.querySelector(".root")){e.n=2;break}return e.a(2);case 2:a=(0,m.A)(t.children),e.p=3,a.s();case 4:if((r=a.n()).done){e.n=7;break}if("HA-ALERT"===(o=r.value).tagName){e.n=6;break}if(!(o instanceof $.mN)){e.n=5;break}return e.n=5,o.updateComplete;case 5:return o.focus(),e.a(3,7);case 6:e.n=4;break;case 7:e.n=9;break;case 8:e.p=8,i=e.v,a.e(i);case 9:return e.p=9,a.f(),e.f(9);case 10:return e.a(2)}}),e,this,[[3,8,9,10]])}))),function(){return a.apply(this,arguments)})},{key:"willUpdate",value:function(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{var t;"selector"in e||null===(t=x[e.type])||void 0===t||t.call(x)}))}},{key:"render",value:function(){return(0,$.qy)(r||(r=M`
      <div class="root" part="root">
        ${0}
        ${0}
      </div>
    `),this.error&&this.error.base?(0,$.qy)(o||(o=M`
              <ha-alert alert-type="error">
                ${0}
              </ha-alert>
            `),this._computeError(this.error.base,this.schema)):"",this.schema.map((e=>{var t,a=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),r=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return(0,$.qy)(i||(i=M`
            ${0}
            ${0}
          `),a?(0,$.qy)(n||(n=M`
                  <ha-alert own-margin alert-type="error">
                    ${0}
                  </ha-alert>
                `),this._computeError(a,e)):r?(0,$.qy)(s||(s=M`
                    <ha-alert own-margin alert-type="warning">
                      ${0}
                    </ha-alert>
                  `),this._computeWarning(r,e)):"","selector"in e?(0,$.qy)(l||(l=M`<ha-selector
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
                ></ha-selector>`),e,this.hass,this.narrow,e.name,e.selector,L(this.data,e),this._computeLabel(e,this.data),e.disabled||this.disabled||!1,e.required?void 0:e.default,this._computeHelper(e),this.localizeValue,e.required||!1,this._generateContext(e)):(0,w._)(this.fieldElementName(e.type),Object.assign({schema:e,data:L(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:null===(t=this.hass)||void 0===t?void 0:t.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e)},this.getFormProperties())))})))}},{key:"fieldElementName",value:function(e){return`ha-form-${e}`}},{key:"_generateContext",value:function(e){if(e.context){for(var t={},a=0,r=Object.entries(e.context);a<r.length;a++){var o=(0,d.A)(r[a],2),i=o[0],n=o[1];t[i]=this.data[n]}return t}}},{key:"createRenderRoot",value:function(){var e=(0,g.A)(t,"createRenderRoot",this,3)([]);return this.addValueChangedListener(e),e}},{key:"addValueChangedListener",value:function(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();var t=e.target.schema;if(e.target!==this){var a=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data=Object.assign(Object.assign({},this.data),a),(0,E.r)(this,"value-changed",{value:this.data})}}))}},{key:"_computeLabel",value:function(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}},{key:"_computeHelper",value:function(e){return this.computeHelper?this.computeHelper(e):""}},{key:"_computeError",value:function(e,t){return Array.isArray(e)?(0,$.qy)(c||(c=M`<ul>
        ${0}
      </ul>`),e.map((e=>(0,$.qy)(u||(u=M`<li>
              ${0}
            </li>`),this.computeError?this.computeError(e,t):e)))):this.computeError?this.computeError(e,t):e}},{key:"_computeWarning",value:function(e,t){return this.computeWarning?this.computeWarning(e,t):e}}]);var a}($.WF);q.shadowRootOptions={mode:"open",delegatesFocus:!0},q.styles=(0,$.AH)(h||(h=M`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `)),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,k.__decorate)([(0,A.MZ)({type:Boolean})],q.prototype,"narrow",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"data",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"schema",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"error",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"warning",void 0),(0,k.__decorate)([(0,A.MZ)({type:Boolean})],q.prototype,"disabled",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"computeError",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"computeWarning",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"computeLabel",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"computeHelper",void 0),(0,k.__decorate)([(0,A.MZ)({attribute:!1})],q.prototype,"localizeValue",void 0),q=(0,k.__decorate)([(0,A.EM)("ha-form")],q)},33506:function(e,t,a){a.a(e,(async function(e,r){try{a.r(t),a.d(t,{DialogForm:function(){return k}});var o=a(61397),i=a(50264),n=a(44734),s=a(56038),l=a(69683),c=a(6454),u=(a(28706),a(62826)),h=a(96196),d=a(77845),p=a(92542),m=a(89473),_=a(95637),v=(a(91120),a(39396)),b=e([m]);m=(b.then?(await b)():b)[0];var y,f,g=e=>e,k=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,l.A)(this,t,[].concat(r)))._data={},e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"showDialog",value:(a=(0,i.A)((0,o.A)().m((function e(t){return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:this._params=t,this._data=t.data||{};case 1:return e.a(2)}}),e,this)}))),function(e){return a.apply(this,arguments)})},{key:"closeDialog",value:function(){return this._params=void 0,this._data={},(0,p.r)(this,"dialog-closed",{dialog:this.localName}),!0}},{key:"_submit",value:function(){var e,t;null===(e=this._params)||void 0===e||null===(t=e.submit)||void 0===t||t.call(e,this._data),this.closeDialog()}},{key:"_cancel",value:function(){var e,t;null===(e=this._params)||void 0===e||null===(t=e.cancel)||void 0===t||t.call(e),this.closeDialog()}},{key:"_valueChanged",value:function(e){this._data=e.detail.value}},{key:"render",value:function(){return this._params&&this.hass?(0,h.qy)(y||(y=g`
      <ha-dialog
        open
        scrimClickAction
        escapeKeyAction
        .heading=${0}
        @closed=${0}
      >
        <ha-form
          dialogInitialFocus
          .hass=${0}
          .computeLabel=${0}
          .computeHelper=${0}
          .data=${0}
          .schema=${0}
          @value-changed=${0}
        >
        </ha-form>
        <ha-button
          appearance="plain"
          @click=${0}
          slot="secondaryAction"
        >
          ${0}
        </ha-button>
        <ha-button @click=${0} slot="primaryAction">
          ${0}
        </ha-button>
      </ha-dialog>
    `),(0,_.l)(this.hass,this._params.title),this._cancel,this.hass,this._params.computeLabel,this._params.computeHelper,this._data,this._params.schema,this._valueChanged,this._cancel,this._params.cancelText||this.hass.localize("ui.common.cancel"),this._submit,this._params.submitText||this.hass.localize("ui.common.save")):h.s6}}]);var a}(h.WF);k.styles=[v.nA,(0,h.AH)(f||(f=g``))],(0,u.__decorate)([(0,d.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,u.__decorate)([(0,d.wk)()],k.prototype,"_params",void 0),(0,u.__decorate)([(0,d.wk)()],k.prototype,"_data",void 0),k=(0,u.__decorate)([(0,d.EM)("dialog-form")],k),r()}catch($){r($)}}))}}]);
//# sourceMappingURL=5919.234b4c3de1552da7.js.map