export const __webpack_id__="1850";export const __webpack_ids__=["1850"];export const __webpack_modules__={91120:function(e,t,a){var o=a(62826),r=a(96196),i=a(77845),n=a(51757),l=a(92542);a(17963),a(87156);const s={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},c=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null;class d extends r.WF{getFormProperties(){return{}}async focus(){await this.updateComplete;const e=this.renderRoot.querySelector(".root");if(e)for(const t of e.children)if("HA-ALERT"!==t.tagName){t instanceof r.mN&&await t.updateComplete,t.focus();break}}willUpdate(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{"selector"in e||s[e.type]?.()}))}render(){return r.qy`
      <div class="root" part="root">
        ${this.error&&this.error.base?r.qy`
              <ha-alert alert-type="error">
                ${this._computeError(this.error.base,this.schema)}
              </ha-alert>
            `:""}
        ${this.schema.map((e=>{const t=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),a=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return r.qy`
            ${t?r.qy`
                  <ha-alert own-margin alert-type="error">
                    ${this._computeError(t,e)}
                  </ha-alert>
                `:a?r.qy`
                    <ha-alert own-margin alert-type="warning">
                      ${this._computeWarning(a,e)}
                    </ha-alert>
                  `:""}
            ${"selector"in e?r.qy`<ha-selector
                  .schema=${e}
                  .hass=${this.hass}
                  .narrow=${this.narrow}
                  .name=${e.name}
                  .selector=${e.selector}
                  .value=${c(this.data,e)}
                  .label=${this._computeLabel(e,this.data)}
                  .disabled=${e.disabled||this.disabled||!1}
                  .placeholder=${e.required?void 0:e.default}
                  .helper=${this._computeHelper(e)}
                  .localizeValue=${this.localizeValue}
                  .required=${e.required||!1}
                  .context=${this._generateContext(e)}
                ></ha-selector>`:(0,n._)(this.fieldElementName(e.type),{schema:e,data:c(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:this.hass?.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e),...this.getFormProperties()})}
          `}))}
      </div>
    `}fieldElementName(e){return`ha-form-${e}`}_generateContext(e){if(!e.context)return;const t={};for(const[a,o]of Object.entries(e.context))t[a]=this.data[o];return t}createRenderRoot(){const e=super.createRenderRoot();return this.addValueChangedListener(e),e}addValueChangedListener(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();const t=e.target.schema;if(e.target===this)return;const a=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data={...this.data,...a},(0,l.r)(this,"value-changed",{value:this.data})}))}_computeLabel(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}_computeHelper(e){return this.computeHelper?this.computeHelper(e):""}_computeError(e,t){return Array.isArray(e)?r.qy`<ul>
        ${e.map((e=>r.qy`<li>
              ${this.computeError?this.computeError(e,t):e}
            </li>`))}
      </ul>`:this.computeError?this.computeError(e,t):e}_computeWarning(e,t){return this.computeWarning?this.computeWarning(e,t):e}constructor(...e){super(...e),this.narrow=!1,this.disabled=!1}}d.shadowRootOptions={mode:"open",delegatesFocus:!0},d.styles=r.AH`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `,(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean})],d.prototype,"narrow",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"data",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"schema",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"error",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"warning",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean})],d.prototype,"disabled",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"computeError",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"computeWarning",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"computeLabel",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"computeHelper",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"localizeValue",void 0),d=(0,o.__decorate)([(0,i.EM)("ha-form")],d)},49100:function(e,t,a){a.r(t),a.d(t,{HaSelectorSelector:()=>d});var o=a(62826),r=a(96196),i=a(77845),n=a(22786),l=a(92542);a(91120);const s={number:{min:1,max:100}},c={action:[],area:[{name:"multiple",selector:{boolean:{}}}],attribute:[{name:"entity_id",selector:{entity:{}}}],boolean:[],color_temp:[{name:"unit",selector:{select:{options:["kelvin","mired"]}}},{name:"min",selector:{number:{mode:"box"}}},{name:"max",selector:{number:{mode:"box"}}}],condition:[],date:[],datetime:[],device:[{name:"multiple",selector:{boolean:{}}}],duration:[{name:"enable_day",selector:{boolean:{}}},{name:"enable_millisecond",selector:{boolean:{}}}],entity:[{name:"multiple",selector:{boolean:{}}}],floor:[{name:"multiple",selector:{boolean:{}}}],icon:[],location:[],media:[{name:"accept",selector:{text:{multiple:!0}}}],number:[{name:"min",selector:{number:{mode:"box",step:"any"}}},{name:"max",selector:{number:{mode:"box",step:"any"}}},{name:"step",selector:{number:{mode:"box",step:"any"}}}],object:[],color_rgb:[],select:[{name:"options",selector:{object:{}}},{name:"multiple",selector:{boolean:{}}}],state:[{name:"entity_id",selector:{entity:{}}},{name:"multiple",selector:{boolean:{}}}],target:[],template:[],text:[{name:"multiple",selector:{boolean:{}}},{name:"multiline",selector:{boolean:{}}},{name:"prefix",selector:{text:{}}},{name:"suffix",selector:{text:{}}}],theme:[],time:[]};class d extends r.WF{shouldUpdate(e){return 1!==e.size||!e.has("hass")}render(){let e,t;if(this._yamlMode)t="manual",e={type:t,manual:this.value};else{t=Object.keys(this.value)[0];const a=Object.values(this.value)[0];e={type:t,..."object"==typeof a?a:[]}}const a=this._schema(t,this.hass.localize);return r.qy`<div>
      <p>${this.label?this.label:""}</p>
      <ha-form
        .hass=${this.hass}
        .data=${e}
        .schema=${a}
        .computeLabel=${this._computeLabelCallback}
        @value-changed=${this._valueChanged}
        .narrow=${this.narrow}
      ></ha-form>
    </div>`}_valueChanged(e){e.stopPropagation();const t=e.detail.value,a=t.type;if(!a||"object"!=typeof t||0===Object.keys(t).length)return;const o=Object.keys(this.value)[0];if("manual"===a&&!this._yamlMode)return this._yamlMode=!0,void this.requestUpdate();if("manual"===a&&void 0===t.manual)return;let r;"manual"!==a&&(this._yamlMode=!1),delete t.type,r="manual"===a?t.manual:a===o?{[a]:{...t.manual?t.manual[o]:t}}:{[a]:{...s[a]}},(0,l.r)(this,"value-changed",{value:r})}constructor(...e){super(...e),this.disabled=!1,this.narrow=!1,this.required=!0,this._yamlMode=!1,this._schema=(0,n.A)(((e,t)=>[{name:"type",required:!0,selector:{select:{mode:"dropdown",options:Object.keys(c).concat("manual").map((e=>({label:t(`ui.components.selectors.selector.types.${e}`)||e,value:e})))}}},..."manual"===e?[{name:"manual",selector:{object:{}}}]:[],...c[e]?c[e].length>1?[{name:"",type:"expandable",title:t("ui.components.selectors.selector.options"),schema:c[e]}]:c[e]:[]])),this._computeLabelCallback=e=>this.hass.localize(`ui.components.selectors.selector.${e.name}`)||e.name}}d.styles=r.AH`
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
  `,(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,o.__decorate)([(0,i.MZ)({attribute:!1})],d.prototype,"value",void 0),(0,o.__decorate)([(0,i.MZ)()],d.prototype,"label",void 0),(0,o.__decorate)([(0,i.MZ)()],d.prototype,"helper",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0})],d.prototype,"disabled",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean})],d.prototype,"narrow",void 0),(0,o.__decorate)([(0,i.MZ)({type:Boolean,reflect:!0})],d.prototype,"required",void 0),d=(0,o.__decorate)([(0,i.EM)("ha-selector-selector")],d)}};
//# sourceMappingURL=1850.9d3bf3ceaf4b4619.js.map