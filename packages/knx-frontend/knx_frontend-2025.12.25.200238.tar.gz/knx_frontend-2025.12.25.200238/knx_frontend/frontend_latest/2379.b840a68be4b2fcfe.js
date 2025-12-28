export const __webpack_id__="2379";export const __webpack_ids__=["2379"];export const __webpack_modules__={88867:function(e,i,t){t.r(i),t.d(i,{HaIconPicker:()=>u});var a=t(62826),o=t(96196),s=t(77845),l=t(22786),r=t(92542),n=t(33978);t(34887),t(22598),t(94343);let d=[],h=!1;const c=async e=>{try{const i=n.y[e].getIconList;if("function"!=typeof i)return[];const t=await i();return t.map((i=>({icon:`${e}:${i.name}`,parts:new Set(i.name.split("-")),keywords:i.keywords??[]})))}catch(i){return console.warn(`Unable to load icon list for ${e} iconset`),[]}},p=e=>o.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${e.icon} slot="start"></ha-icon>
    ${e.icon}
  </ha-combo-box-item>
`;class u extends o.WF{render(){return o.qy`
      <ha-combo-box
        .hass=${this.hass}
        item-value-path="icon"
        item-label-path="icon"
        .value=${this._value}
        allow-custom-value
        .dataProvider=${h?this._iconProvider:void 0}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        .placeholder=${this.placeholder}
        .errorMessage=${this.errorMessage}
        .invalid=${this.invalid}
        .renderer=${p}
        icon
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
      >
        ${this._value||this.placeholder?o.qy`
              <ha-icon .icon=${this._value||this.placeholder} slot="icon">
              </ha-icon>
            `:o.qy`<slot slot="icon" name="fallback"></slot>`}
      </ha-combo-box>
    `}async _openedChanged(e){e.detail.value&&!h&&(await(async()=>{h=!0;const e=await t.e("3451").then(t.t.bind(t,83174,19));d=e.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords})));const i=[];Object.keys(n.y).forEach((e=>{i.push(c(e))})),(await Promise.all(i)).forEach((e=>{d.push(...e)}))})(),this.requestUpdate())}_valueChanged(e){e.stopPropagation(),this._setValue(e.detail.value)}_setValue(e){this.value=e,(0,r.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}get _value(){return this.value||""}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.invalid=!1,this._filterIcons=(0,l.A)(((e,i=d)=>{if(!e)return i;const t=[],a=(e,i)=>t.push({icon:e,rank:i});for(const o of i)o.parts.has(e)?a(o.icon,1):o.keywords.includes(e)?a(o.icon,2):o.icon.includes(e)?a(o.icon,3):o.keywords.some((i=>i.includes(e)))&&a(o.icon,4);return 0===t.length&&a(e,0),t.sort(((e,i)=>e.rank-i.rank))})),this._iconProvider=(e,i)=>{const t=this._filterIcons(e.filter.toLowerCase(),d),a=e.page*e.pageSize,o=a+e.pageSize;i(t.slice(a,o),t.length)}}}u.styles=o.AH`
    *[slot="icon"] {
      color: var(--primary-text-color);
      position: relative;
      bottom: 2px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `,(0,a.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,a.__decorate)([(0,s.MZ)()],u.prototype,"value",void 0),(0,a.__decorate)([(0,s.MZ)()],u.prototype,"label",void 0),(0,a.__decorate)([(0,s.MZ)()],u.prototype,"helper",void 0),(0,a.__decorate)([(0,s.MZ)()],u.prototype,"placeholder",void 0),(0,a.__decorate)([(0,s.MZ)({attribute:"error-message"})],u.prototype,"errorMessage",void 0),(0,a.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,a.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,a.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"invalid",void 0),u=(0,a.__decorate)([(0,s.EM)("ha-icon-picker")],u)},77238:function(e,i,t){t.r(i);var a=t(62826),o=t(96196),s=t(77845),l=t(92542),r=(t(34811),t(88867),t(7153),t(78740),t(39396));class n extends o.WF{set item(e){this._item=e,e?(this._name=e.name||"",this._icon=e.icon||"",this._maximum=e.maximum??void 0,this._minimum=e.minimum??void 0,this._restore=e.restore??!0,this._step=e.step??1,this._initial=e.initial??0):(this._name="",this._icon="",this._maximum=void 0,this._minimum=void 0,this._restore=!0,this._step=1,this._initial=0)}focus(){this.updateComplete.then((()=>this.shadowRoot?.querySelector("[dialogInitialFocus]")?.focus()))}render(){return this.hass?o.qy`
      <div class="form">
        <ha-textfield
          .value=${this._name}
          .configValue=${"name"}
          @input=${this._valueChanged}
          .label=${this.hass.localize("ui.dialogs.helper_settings.generic.name")}
          autoValidate
          required
          .validationMessage=${this.hass.localize("ui.dialogs.helper_settings.required_error_msg")}
          dialogInitialFocus
          .disabled=${this.disabled}
        ></ha-textfield>
        <ha-icon-picker
          .hass=${this.hass}
          .value=${this._icon}
          .configValue=${"icon"}
          @value-changed=${this._valueChanged}
          .label=${this.hass.localize("ui.dialogs.helper_settings.generic.icon")}
          .disabled=${this.disabled}
        ></ha-icon-picker>
        <ha-textfield
          .value=${this._minimum}
          .configValue=${"minimum"}
          type="number"
          @input=${this._valueChanged}
          .label=${this.hass.localize("ui.dialogs.helper_settings.counter.minimum")}
          .disabled=${this.disabled}
        ></ha-textfield>
        <ha-textfield
          .value=${this._maximum}
          .configValue=${"maximum"}
          type="number"
          @input=${this._valueChanged}
          .label=${this.hass.localize("ui.dialogs.helper_settings.counter.maximum")}
          .disabled=${this.disabled}
        ></ha-textfield>
        <ha-textfield
          .value=${this._initial}
          .configValue=${"initial"}
          type="number"
          @input=${this._valueChanged}
          .label=${this.hass.localize("ui.dialogs.helper_settings.counter.initial")}
          .disabled=${this.disabled}
        ></ha-textfield>
        <ha-expansion-panel
          header=${this.hass.localize("ui.dialogs.helper_settings.generic.advanced_settings")}
          outlined
        >
          <ha-textfield
            .value=${this._step}
            .configValue=${"step"}
            type="number"
            @input=${this._valueChanged}
            .label=${this.hass.localize("ui.dialogs.helper_settings.counter.step")}
            .disabled=${this.disabled}
          ></ha-textfield>
          <div class="row">
            <ha-switch
              .checked=${this._restore}
              .configValue=${"restore"}
              @change=${this._valueChanged}
              .disabled=${this.disabled}
            >
            </ha-switch>
            <div>
              ${this.hass.localize("ui.dialogs.helper_settings.counter.restore")}
            </div>
          </div>
        </ha-expansion-panel>
      </div>
    `:o.s6}_valueChanged(e){if(!this.new&&!this._item)return;e.stopPropagation();const i=e.target,t=i.configValue,a="number"===i.type?""!==i.value?Number(i.value):void 0:"ha-switch"===i.localName?e.target.checked:e.detail?.value||i.value;if(this[`_${t}`]===a)return;const o={...this._item};void 0===a||""===a?delete o[t]:o[t]=a,(0,l.r)(this,"value-changed",{value:o})}static get styles(){return[r.RF,o.AH`
        .form {
          color: var(--primary-text-color);
        }
        .row {
          margin-top: 12px;
          margin-bottom: 12px;
          color: var(--primary-text-color);
          display: flex;
          align-items: center;
        }
        .row div {
          margin-left: 16px;
          margin-inline-start: 16px;
          margin-inline-end: initial;
        }
        ha-textfield {
          display: block;
          margin: 8px 0;
        }
      `]}constructor(...e){super(...e),this.new=!1,this.disabled=!1}}(0,a.__decorate)([(0,s.MZ)({attribute:!1})],n.prototype,"hass",void 0),(0,a.__decorate)([(0,s.MZ)({type:Boolean})],n.prototype,"new",void 0),(0,a.__decorate)([(0,s.MZ)({type:Boolean})],n.prototype,"disabled",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_name",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_icon",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_maximum",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_minimum",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_restore",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_initial",void 0),(0,a.__decorate)([(0,s.wk)()],n.prototype,"_step",void 0),n=(0,a.__decorate)([(0,s.EM)("ha-counter-form")],n)}};
//# sourceMappingURL=2379.b840a68be4b2fcfe.js.map