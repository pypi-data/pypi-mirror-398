export const __webpack_id__="1364";export const __webpack_ids__=["1364"];export const __webpack_modules__={28175:function(e,t,a){a.a(e,(async function(e,i){try{a.r(t),a.d(t,{HaFormInteger:()=>c});var s=a(62826),h=a(96196),d=a(77845),l=a(92542),r=a(60808),o=(a(70524),a(56768),a(78740),e([r]));r=(o.then?(await o)():o)[0];class c extends h.WF{focus(){this._input&&this._input.focus()}render(){return void 0!==this.schema.valueMin&&void 0!==this.schema.valueMax&&this.schema.valueMax-this.schema.valueMin<256?h.qy`
        <div>
          ${this.label}
          <div class="flex">
            ${this.schema.required?"":h.qy`
                  <ha-checkbox
                    @change=${this._handleCheckboxChange}
                    .checked=${void 0!==this.data}
                    .disabled=${this.disabled}
                  ></ha-checkbox>
                `}
            <ha-slider
              labeled
              .value=${this._value}
              .min=${this.schema.valueMin}
              .max=${this.schema.valueMax}
              .disabled=${this.disabled||void 0===this.data&&!this.schema.required}
              @change=${this._valueChanged}
            ></ha-slider>
          </div>
          ${this.helper?h.qy`<ha-input-helper-text .disabled=${this.disabled}
                >${this.helper}</ha-input-helper-text
              >`:""}
        </div>
      `:h.qy`
      <ha-textfield
        type="number"
        inputMode="numeric"
        .label=${this.label}
        .helper=${this.helper}
        helperPersistent
        .value=${void 0!==this.data?this.data:""}
        .disabled=${this.disabled}
        .required=${this.schema.required}
        .autoValidate=${this.schema.required}
        .suffix=${this.schema.description?.suffix}
        .validationMessage=${this.schema.required?this.localize?.("ui.common.error_required"):void 0}
        @input=${this._valueChanged}
      ></ha-textfield>
    `}updated(e){e.has("schema")&&this.toggleAttribute("own-margin",!("valueMin"in this.schema&&"valueMax"in this.schema||!this.schema.required))}get _value(){return void 0!==this.data?this.data:this.schema.required?void 0!==this.schema.description?.suggested_value&&null!==this.schema.description?.suggested_value||this.schema.default||this.schema.valueMin||0:this.schema.valueMin||0}_handleCheckboxChange(e){let t;if(e.target.checked){for(const a of[this._lastValue,this.schema.description?.suggested_value,this.schema.default,0])if(void 0!==a){t=a;break}}else this._lastValue=this.data;(0,l.r)(this,"value-changed",{value:t})}_valueChanged(e){const t=e.target,a=t.value;let i;if(""!==a&&(i=parseInt(String(a))),this.data!==i)(0,l.r)(this,"value-changed",{value:i});else{const e=void 0===i?"":String(i);t.value!==e&&(t.value=e)}}constructor(...e){super(...e),this.disabled=!1}}c.styles=h.AH`
    :host([own-margin]) {
      margin-bottom: 5px;
    }
    .flex {
      display: flex;
    }
    ha-slider {
      flex: 1;
    }
    ha-textfield {
      display: block;
    }
  `,(0,s.__decorate)([(0,d.MZ)({attribute:!1})],c.prototype,"localize",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],c.prototype,"schema",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],c.prototype,"data",void 0),(0,s.__decorate)([(0,d.MZ)()],c.prototype,"label",void 0),(0,s.__decorate)([(0,d.MZ)()],c.prototype,"helper",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,s.__decorate)([(0,d.P)("ha-textfield ha-slider")],c.prototype,"_input",void 0),c=(0,s.__decorate)([(0,d.EM)("ha-form-integer")],c),i()}catch(c){i(c)}}))}};
//# sourceMappingURL=1364.3b10017d531dbac0.js.map