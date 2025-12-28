export const __webpack_id__="4297";export const __webpack_ids__=["4297"];export const __webpack_modules__={91120:function(e,t,a){var o=a(62826),r=a(96196),s=a(77845),i=a(51757),n=a(92542);a(17963),a(87156);const l={boolean:()=>a.e("2018").then(a.bind(a,49337)),constant:()=>a.e("9938").then(a.bind(a,37449)),float:()=>a.e("812").then(a.bind(a,5863)),grid:()=>a.e("798").then(a.bind(a,81213)),expandable:()=>a.e("8550").then(a.bind(a,29989)),integer:()=>a.e("1364").then(a.bind(a,28175)),multi_select:()=>Promise.all([a.e("2016"),a.e("3616")]).then(a.bind(a,59827)),positive_time_period_dict:()=>a.e("5846").then(a.bind(a,19797)),select:()=>a.e("6262").then(a.bind(a,29317)),string:()=>a.e("8389").then(a.bind(a,33092)),optional_actions:()=>a.e("1454").then(a.bind(a,2173))},c=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null;class h extends r.WF{getFormProperties(){return{}}async focus(){await this.updateComplete;const e=this.renderRoot.querySelector(".root");if(e)for(const t of e.children)if("HA-ALERT"!==t.tagName){t instanceof r.mN&&await t.updateComplete,t.focus();break}}willUpdate(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{"selector"in e||l[e.type]?.()}))}render(){return r.qy`
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
                ></ha-selector>`:(0,i._)(this.fieldElementName(e.type),{schema:e,data:c(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:this.hass?.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e),...this.getFormProperties()})}
          `}))}
      </div>
    `}fieldElementName(e){return`ha-form-${e}`}_generateContext(e){if(!e.context)return;const t={};for(const[a,o]of Object.entries(e.context))t[a]=this.data[o];return t}createRenderRoot(){const e=super.createRenderRoot();return this.addValueChangedListener(e),e}addValueChangedListener(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();const t=e.target.schema;if(e.target===this)return;const a=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data={...this.data,...a},(0,n.r)(this,"value-changed",{value:this.data})}))}_computeLabel(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}_computeHelper(e){return this.computeHelper?this.computeHelper(e):""}_computeError(e,t){return Array.isArray(e)?r.qy`<ul>
        ${e.map((e=>r.qy`<li>
              ${this.computeError?this.computeError(e,t):e}
            </li>`))}
      </ul>`:this.computeError?this.computeError(e,t):e}_computeWarning(e,t){return this.computeWarning?this.computeWarning(e,t):e}constructor(...e){super(...e),this.narrow=!1,this.disabled=!1}}h.shadowRootOptions={mode:"open",delegatesFocus:!0},h.styles=r.AH`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `,(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],h.prototype,"narrow",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"data",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"schema",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"error",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"warning",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],h.prototype,"disabled",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"computeError",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"computeWarning",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"computeLabel",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"computeHelper",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"localizeValue",void 0),h=(0,o.__decorate)([(0,s.EM)("ha-form")],h)},88240:function(e,t,a){a.a(e,(async function(e,o){try{a.r(t);var r=a(62826),s=a(96196),i=a(22786),n=a(77845),l=a(92542),c=a(95637),h=(a(91120),a(89473)),d=a(39396),p=e([h]);h=(p.then?(await p)():p)[0];class u extends s.WF{showDialog(e){this._params=e,this._error=void 0,this._data=e.block,this._expand=!!e.block?.data}closeDialog(){this._params=void 0,this._data=void 0,(0,l.r)(this,"dialog-closed",{dialog:this.localName})}render(){return this._params&&this._data?s.qy`
      <ha-dialog
        open
        @closed=${this.closeDialog}
        .heading=${(0,c.l)(this.hass,this.hass.localize("ui.dialogs.helper_settings.schedule.edit_schedule_block"))}
      >
        <div>
          <ha-form
            .hass=${this.hass}
            .schema=${this._schema(this._expand)}
            .data=${this._data}
            .error=${this._error}
            .computeLabel=${this._computeLabelCallback}
            @value-changed=${this._valueChanged}
          ></ha-form>
        </div>
        <ha-button
          slot="secondaryAction"
          @click=${this._deleteBlock}
          appearance="plain"
          variant="danger"
        >
          ${this.hass.localize("ui.common.delete")}
        </ha-button>
        <ha-button slot="primaryAction" @click=${this._updateBlock}>
          ${this.hass.localize("ui.common.save")}
        </ha-button>
      </ha-dialog>
    `:s.s6}_valueChanged(e){this._error=void 0,this._data=e.detail.value}_updateBlock(){try{this._params.updateBlock(this._data),this.closeDialog()}catch(e){this._error={base:e?e.message:"Unknown error"}}}_deleteBlock(){try{this._params.deleteBlock(),this.closeDialog()}catch(e){this._error={base:e?e.message:"Unknown error"}}}static get styles(){return[d.nA]}constructor(...e){super(...e),this._expand=!1,this._schema=(0,i.A)((e=>[{name:"from",required:!0,selector:{time:{no_second:!0}}},{name:"to",required:!0,selector:{time:{no_second:!0}}},{name:"advanced_settings",type:"expandable",flatten:!0,expanded:e,schema:[{name:"data",required:!1,selector:{object:{}}}]}])),this._computeLabelCallback=e=>{switch(e.name){case"from":return this.hass.localize("ui.dialogs.helper_settings.schedule.start");case"to":return this.hass.localize("ui.dialogs.helper_settings.schedule.end");case"data":return this.hass.localize("ui.dialogs.helper_settings.schedule.data");case"advanced_settings":return this.hass.localize("ui.dialogs.helper_settings.generic.advanced_settings")}return""}}}(0,r.__decorate)([(0,n.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,r.__decorate)([(0,n.wk)()],u.prototype,"_error",void 0),(0,r.__decorate)([(0,n.wk)()],u.prototype,"_data",void 0),(0,r.__decorate)([(0,n.wk)()],u.prototype,"_params",void 0),customElements.define("dialog-schedule-block-info",u),o()}catch(u){o(u)}}))}};
//# sourceMappingURL=4297.3f92862bd2a81d67.js.map