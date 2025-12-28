export const __webpack_id__="4358";export const __webpack_ids__=["4358"];export const __webpack_modules__={88867:function(e,t,i){i.r(t),i.d(t,{HaIconPicker:()=>u});var o=i(62826),a=i(96196),s=i(77845),n=i(22786),l=i(92542),r=i(33978);i(34887),i(22598),i(94343);let d=[],c=!1;const h=async e=>{try{const t=r.y[e].getIconList;if("function"!=typeof t)return[];const i=await t();return i.map((t=>({icon:`${e}:${t.name}`,parts:new Set(t.name.split("-")),keywords:t.keywords??[]})))}catch(t){return console.warn(`Unable to load icon list for ${e} iconset`),[]}},p=e=>a.qy`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${e.icon} slot="start"></ha-icon>
    ${e.icon}
  </ha-combo-box-item>
`;class u extends a.WF{render(){return a.qy`
      <ha-combo-box
        .hass=${this.hass}
        item-value-path="icon"
        item-label-path="icon"
        .value=${this._value}
        allow-custom-value
        .dataProvider=${c?this._iconProvider:void 0}
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
        ${this._value||this.placeholder?a.qy`
              <ha-icon .icon=${this._value||this.placeholder} slot="icon">
              </ha-icon>
            `:a.qy`<slot slot="icon" name="fallback"></slot>`}
      </ha-combo-box>
    `}async _openedChanged(e){e.detail.value&&!c&&(await(async()=>{c=!0;const e=await i.e("3451").then(i.t.bind(i,83174,19));d=e.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords})));const t=[];Object.keys(r.y).forEach((e=>{t.push(h(e))})),(await Promise.all(t)).forEach((e=>{d.push(...e)}))})(),this.requestUpdate())}_valueChanged(e){e.stopPropagation(),this._setValue(e.detail.value)}_setValue(e){this.value=e,(0,l.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}get _value(){return this.value||""}constructor(...e){super(...e),this.disabled=!1,this.required=!1,this.invalid=!1,this._filterIcons=(0,n.A)(((e,t=d)=>{if(!e)return t;const i=[],o=(e,t)=>i.push({icon:e,rank:t});for(const a of t)a.parts.has(e)?o(a.icon,1):a.keywords.includes(e)?o(a.icon,2):a.icon.includes(e)?o(a.icon,3):a.keywords.some((t=>t.includes(e)))&&o(a.icon,4);return 0===i.length&&o(e,0),i.sort(((e,t)=>e.rank-t.rank))})),this._iconProvider=(e,t)=>{const i=this._filterIcons(e.filter.toLowerCase(),d),o=e.page*e.pageSize,a=o+e.pageSize;t(i.slice(o,a),i.length)}}}u.styles=a.AH`
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
  `,(0,o.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,o.__decorate)([(0,s.MZ)()],u.prototype,"value",void 0),(0,o.__decorate)([(0,s.MZ)()],u.prototype,"label",void 0),(0,o.__decorate)([(0,s.MZ)()],u.prototype,"helper",void 0),(0,o.__decorate)([(0,s.MZ)()],u.prototype,"placeholder",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:"error-message"})],u.prototype,"errorMessage",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"invalid",void 0),u=(0,o.__decorate)([(0,s.EM)("ha-icon-picker")],u)},24933:function(e,t,i){i.a(e,(async function(e,o){try{i.r(t);var a=i(62826),s=i(96196),n=i(77845),l=i(4937),r=i(92542),d=i(89473),c=(i(60733),i(88867),i(75261),i(56565),i(63801),i(78740),i(10234)),h=i(39396),p=e([d]);d=(p.then?(await p)():p)[0];const u="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",_="M21 11H3V9H21V11M21 13H3V15H21V13Z";class v extends s.WF{_optionMoved(e){e.stopPropagation();const{oldIndex:t,newIndex:i}=e.detail,o=this._options.concat(),a=o.splice(t,1)[0];o.splice(i,0,a),(0,r.r)(this,"value-changed",{value:{...this._item,options:o}})}set item(e){this._item=e,e?(this._name=e.name||"",this._icon=e.icon||"",this._options=e.options||[]):(this._name="",this._icon="",this._options=[])}focus(){this.updateComplete.then((()=>this.shadowRoot?.querySelector("[dialogInitialFocus]")?.focus()))}render(){return this.hass?s.qy`
      <div class="form">
        <ha-textfield
          dialogInitialFocus
          autoValidate
          required
          .validationMessage=${this.hass.localize("ui.dialogs.helper_settings.required_error_msg")}
          .value=${this._name}
          .label=${this.hass.localize("ui.dialogs.helper_settings.generic.name")}
          .configValue=${"name"}
          @input=${this._valueChanged}
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
        <div class="header">
          ${this.hass.localize("ui.dialogs.helper_settings.input_select.options")}:
        </div>
        <ha-sortable
          @item-moved=${this._optionMoved}
          handle-selector=".handle"
          .disabled=${this.disabled}
        >
          <ha-list class="options">
            ${this._options.length?(0,l.u)(this._options,(e=>e),((e,t)=>s.qy`
                    <ha-list-item class="option" hasMeta>
                      <div class="optioncontent">
                        <div class="handle">
                          <ha-svg-icon
                            .path=${_}
                          ></ha-svg-icon>
                        </div>
                        ${e}
                      </div>
                      <ha-icon-button
                        slot="meta"
                        .index=${t}
                        .label=${this.hass.localize("ui.dialogs.helper_settings.input_select.remove_option")}
                        @click=${this._removeOption}
                        .disabled=${this.disabled}
                        .path=${u}
                      ></ha-icon-button>
                    </ha-list-item>
                  `)):s.qy`
                  <ha-list-item noninteractive>
                    ${this.hass.localize("ui.dialogs.helper_settings.input_select.no_options")}
                  </ha-list-item>
                `}
          </ha-list>
        </ha-sortable>
        <div class="layout horizontal center">
          <ha-textfield
            class="flex-auto"
            id="option_input"
            .label=${this.hass.localize("ui.dialogs.helper_settings.input_select.add_option")}
            @keydown=${this._handleKeyAdd}
            .disabled=${this.disabled}
          ></ha-textfield>
          <ha-button
            size="small"
            appearance="plain"
            @click=${this._addOption}
            .disabled=${this.disabled}
            >${this.hass.localize("ui.dialogs.helper_settings.input_select.add")}</ha-button
          >
        </div>
      </div>
    `:s.s6}_handleKeyAdd(e){e.stopPropagation(),"Enter"===e.key&&this._addOption()}_addOption(){const e=this._optionInput;e?.value&&((0,r.r)(this,"value-changed",{value:{...this._item,options:[...this._options,e.value]}}),e.value="")}async _removeOption(e){const t=e.target.index;if(!(await(0,c.dk)(this,{title:this.hass.localize("ui.dialogs.helper_settings.input_select.confirm_delete.delete"),text:this.hass.localize("ui.dialogs.helper_settings.input_select.confirm_delete.prompt"),destructive:!0})))return;const i=[...this._options];i.splice(t,1),(0,r.r)(this,"value-changed",{value:{...this._item,options:i}})}_valueChanged(e){if(!this.new&&!this._item)return;e.stopPropagation();const t=e.target.configValue,i=e.detail?.value||e.target.value;if(this[`_${t}`]===i)return;const o={...this._item};i?o[t]=i:delete o[t],(0,r.r)(this,"value-changed",{value:o})}static get styles(){return[h.RF,s.AH`
        .form {
          color: var(--primary-text-color);
        }
        .option {
          border: 1px solid var(--divider-color);
          border-radius: var(--ha-border-radius-sm);
          margin-top: 4px;
          --mdc-icon-button-size: 24px;
          --mdc-ripple-color: transparent;
          --mdc-list-side-padding: 16px;
          cursor: default;
          background-color: var(--card-background-color);
        }
        ha-textfield {
          display: block;
          margin-bottom: 8px;
        }
        #option_input {
          margin-top: 8px;
        }
        .header {
          margin-top: 8px;
          margin-bottom: 8px;
        }
        .handle {
          cursor: move; /* fallback if grab cursor is unsupported */
          cursor: grab;
          padding-right: 12px;
          padding-inline-end: 12px;
          padding-inline-start: initial;
        }
        .handle ha-svg-icon {
          pointer-events: none;
          height: 24px;
        }
        .optioncontent {
          display: flex;
          align-items: center;
        }
      `]}constructor(...e){super(...e),this.new=!1,this.disabled=!1,this._options=[]}}(0,a.__decorate)([(0,n.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],v.prototype,"new",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],v.prototype,"disabled",void 0),(0,a.__decorate)([(0,n.wk)()],v.prototype,"_name",void 0),(0,a.__decorate)([(0,n.wk)()],v.prototype,"_icon",void 0),(0,a.__decorate)([(0,n.wk)()],v.prototype,"_options",void 0),(0,a.__decorate)([(0,n.P)("#option_input",!0)],v.prototype,"_optionInput",void 0),v=(0,a.__decorate)([(0,n.EM)("ha-input_select-form")],v),o()}catch(u){o(u)}}))}};
//# sourceMappingURL=4358.1e0ce42b4b355f37.js.map