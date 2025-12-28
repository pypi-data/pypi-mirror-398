"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4297"],{91120:function(e,t,a){var r,o,i,n,s,l,c,h,d,u=a(78261),p=a(61397),m=a(31432),_=a(50264),v=a(44734),b=a(56038),g=a(69683),y=a(6454),f=a(25460),k=(a(28706),a(23792),a(62062),a(18111),a(7588),a(61701),a(5506),a(26099),a(3362),a(23500),a(62953),a(62826)),$=a(96196),w=a(77845),A=a(51757),x=a(92542),q=(a(17963),a(87156),e=>e),E={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3956"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},L=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null,z=function(e){function t(){var e;(0,v.A)(this,t);for(var a=arguments.length,r=new Array(a),o=0;o<a;o++)r[o]=arguments[o];return(e=(0,g.A)(this,t,[].concat(r))).narrow=!1,e.disabled=!1,e}return(0,y.A)(t,e),(0,b.A)(t,[{key:"getFormProperties",value:function(){return{}}},{key:"focus",value:(a=(0,_.A)((0,p.A)().m((function e(){var t,a,r,o,i;return(0,p.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.n=1,this.updateComplete;case 1:if(t=this.renderRoot.querySelector(".root")){e.n=2;break}return e.a(2);case 2:a=(0,m.A)(t.children),e.p=3,a.s();case 4:if((r=a.n()).done){e.n=7;break}if("HA-ALERT"===(o=r.value).tagName){e.n=6;break}if(!(o instanceof $.mN)){e.n=5;break}return e.n=5,o.updateComplete;case 5:return o.focus(),e.a(3,7);case 6:e.n=4;break;case 7:e.n=9;break;case 8:e.p=8,i=e.v,a.e(i);case 9:return e.p=9,a.f(),e.f(9);case 10:return e.a(2)}}),e,this,[[3,8,9,10]])}))),function(){return a.apply(this,arguments)})},{key:"willUpdate",value:function(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{var t;"selector"in e||null===(t=E[e.type])||void 0===t||t.call(E)}))}},{key:"render",value:function(){return(0,$.qy)(r||(r=q`
      <div class="root" part="root">
        ${0}
        ${0}
      </div>
    `),this.error&&this.error.base?(0,$.qy)(o||(o=q`
              <ha-alert alert-type="error">
                ${0}
              </ha-alert>
            `),this._computeError(this.error.base,this.schema)):"",this.schema.map((e=>{var t,a=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),r=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return(0,$.qy)(i||(i=q`
            ${0}
            ${0}
          `),a?(0,$.qy)(n||(n=q`
                  <ha-alert own-margin alert-type="error">
                    ${0}
                  </ha-alert>
                `),this._computeError(a,e)):r?(0,$.qy)(s||(s=q`
                    <ha-alert own-margin alert-type="warning">
                      ${0}
                    </ha-alert>
                  `),this._computeWarning(r,e)):"","selector"in e?(0,$.qy)(l||(l=q`<ha-selector
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
                ></ha-selector>`),e,this.hass,this.narrow,e.name,e.selector,L(this.data,e),this._computeLabel(e,this.data),e.disabled||this.disabled||!1,e.required?void 0:e.default,this._computeHelper(e),this.localizeValue,e.required||!1,this._generateContext(e)):(0,A._)(this.fieldElementName(e.type),Object.assign({schema:e,data:L(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:null===(t=this.hass)||void 0===t?void 0:t.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e)},this.getFormProperties())))})))}},{key:"fieldElementName",value:function(e){return`ha-form-${e}`}},{key:"_generateContext",value:function(e){if(e.context){for(var t={},a=0,r=Object.entries(e.context);a<r.length;a++){var o=(0,u.A)(r[a],2),i=o[0],n=o[1];t[i]=this.data[n]}return t}}},{key:"createRenderRoot",value:function(){var e=(0,f.A)(t,"createRenderRoot",this,3)([]);return this.addValueChangedListener(e),e}},{key:"addValueChangedListener",value:function(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();var t=e.target.schema;if(e.target!==this){var a=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data=Object.assign(Object.assign({},this.data),a),(0,x.r)(this,"value-changed",{value:this.data})}}))}},{key:"_computeLabel",value:function(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}},{key:"_computeHelper",value:function(e){return this.computeHelper?this.computeHelper(e):""}},{key:"_computeError",value:function(e,t){return Array.isArray(e)?(0,$.qy)(c||(c=q`<ul>
        ${0}
      </ul>`),e.map((e=>(0,$.qy)(h||(h=q`<li>
              ${0}
            </li>`),this.computeError?this.computeError(e,t):e)))):this.computeError?this.computeError(e,t):e}},{key:"_computeWarning",value:function(e,t){return this.computeWarning?this.computeWarning(e,t):e}}]);var a}($.WF);z.shadowRootOptions={mode:"open",delegatesFocus:!0},z.styles=(0,$.AH)(d||(d=q`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `)),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"hass",void 0),(0,k.__decorate)([(0,w.MZ)({type:Boolean})],z.prototype,"narrow",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"data",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"schema",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"error",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"warning",void 0),(0,k.__decorate)([(0,w.MZ)({type:Boolean})],z.prototype,"disabled",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"computeError",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"computeWarning",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"computeLabel",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"computeHelper",void 0),(0,k.__decorate)([(0,w.MZ)({attribute:!1})],z.prototype,"localizeValue",void 0),z=(0,k.__decorate)([(0,w.EM)("ha-form")],z)},88240:function(e,t,a){a.a(e,(async function(e,r){try{a.r(t);var o=a(44734),i=a(56038),n=a(69683),s=a(6454),l=(a(28706),a(62826)),c=a(96196),h=a(22786),d=a(77845),u=a(92542),p=a(95637),m=(a(91120),a(89473)),_=a(39396),v=e([m]);m=(v.then?(await v)():v)[0];var b,g=e=>e,y=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,r=new Array(a),i=0;i<a;i++)r[i]=arguments[i];return(e=(0,n.A)(this,t,[].concat(r)))._expand=!1,e._schema=(0,h.A)((e=>[{name:"from",required:!0,selector:{time:{no_second:!0}}},{name:"to",required:!0,selector:{time:{no_second:!0}}},{name:"advanced_settings",type:"expandable",flatten:!0,expanded:e,schema:[{name:"data",required:!1,selector:{object:{}}}]}])),e._computeLabelCallback=t=>{switch(t.name){case"from":return e.hass.localize("ui.dialogs.helper_settings.schedule.start");case"to":return e.hass.localize("ui.dialogs.helper_settings.schedule.end");case"data":return e.hass.localize("ui.dialogs.helper_settings.schedule.data");case"advanced_settings":return e.hass.localize("ui.dialogs.helper_settings.generic.advanced_settings")}return""},e}return(0,s.A)(t,e),(0,i.A)(t,[{key:"showDialog",value:function(e){var t;this._params=e,this._error=void 0,this._data=e.block,this._expand=!(null===(t=e.block)||void 0===t||!t.data)}},{key:"closeDialog",value:function(){this._params=void 0,this._data=void 0,(0,u.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"render",value:function(){return this._params&&this._data?(0,c.qy)(b||(b=g`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
      >
        <div>
          <ha-form
            .hass=${0}
            .schema=${0}
            .data=${0}
            .error=${0}
            .computeLabel=${0}
            @value-changed=${0}
          ></ha-form>
        </div>
        <ha-button
          slot="secondaryAction"
          @click=${0}
          appearance="plain"
          variant="danger"
        >
          ${0}
        </ha-button>
        <ha-button slot="primaryAction" @click=${0}>
          ${0}
        </ha-button>
      </ha-dialog>
    `),this.closeDialog,(0,p.l)(this.hass,this.hass.localize("ui.dialogs.helper_settings.schedule.edit_schedule_block")),this.hass,this._schema(this._expand),this._data,this._error,this._computeLabelCallback,this._valueChanged,this._deleteBlock,this.hass.localize("ui.common.delete"),this._updateBlock,this.hass.localize("ui.common.save")):c.s6}},{key:"_valueChanged",value:function(e){this._error=void 0,this._data=e.detail.value}},{key:"_updateBlock",value:function(){try{this._params.updateBlock(this._data),this.closeDialog()}catch(e){this._error={base:e?e.message:"Unknown error"}}}},{key:"_deleteBlock",value:function(){try{this._params.deleteBlock(),this.closeDialog()}catch(e){this._error={base:e?e.message:"Unknown error"}}}}],[{key:"styles",get:function(){return[_.nA]}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,l.__decorate)([(0,d.wk)()],y.prototype,"_error",void 0),(0,l.__decorate)([(0,d.wk)()],y.prototype,"_data",void 0),(0,l.__decorate)([(0,d.wk)()],y.prototype,"_params",void 0),customElements.define("dialog-schedule-block-info",y),r()}catch(f){r(f)}}))}}]);
//# sourceMappingURL=4297.d2e692b4d4216acd.js.map