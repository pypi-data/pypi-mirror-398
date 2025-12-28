export const __webpack_id__="4948";export const __webpack_ids__=["4948"];export const __webpack_modules__={99903:function(t,e,o){o.r(e),o.d(e,{HaSelectorAttribute:()=>u});var i=o(62826),a=o(96196),s=o(77845),r=o(92542),d=o(55376);o(34887);class l extends a.WF{shouldUpdate(t){return!(!t.has("_opened")&&this._opened)}updated(t){if(t.has("_opened")&&this._opened||t.has("entityId")||t.has("attribute")){const t=(this.entityId?(0,d.e)(this.entityId):[]).map((t=>{const e=this.hass.states[t];if(!e)return[];return Object.keys(e.attributes).filter((t=>!this.hideAttributes?.includes(t))).map((t=>({value:t,label:this.hass.formatEntityAttributeName(e,t)})))})),e=[],o=new Set;for(const i of t)for(const t of i)o.has(t.value)||(o.add(t.value),e.push(t));this._comboBox.filteredItems=e}}render(){return this.hass?a.qy`
      <ha-combo-box
        .hass=${this.hass}
        .value=${this.value}
        .autofocus=${this.autofocus}
        .label=${this.label??this.hass.localize("ui.components.entity.entity-attribute-picker.attribute")}
        .disabled=${this.disabled||!this.entityId}
        .required=${this.required}
        .helper=${this.helper}
        .allowCustomValue=${this.allowCustomValue}
        item-id-path="value"
        item-value-path="value"
        item-label-path="label"
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
      >
      </ha-combo-box>
    `:a.s6}get _value(){return this.value||""}_openedChanged(t){this._opened=t.detail.value}_valueChanged(t){t.stopPropagation();const e=t.detail.value;e!==this._value&&this._setValue(e)}_setValue(t){this.value=t,setTimeout((()=>{(0,r.r)(this,"value-changed",{value:t}),(0,r.r)(this,"change")}),0)}constructor(...t){super(...t),this.autofocus=!1,this.disabled=!1,this.required=!1,this._opened=!1}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"entityId",void 0),(0,i.__decorate)([(0,s.MZ)({type:Array,attribute:"hide-attributes"})],l.prototype,"hideAttributes",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],l.prototype,"autofocus",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],l.prototype,"disabled",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],l.prototype,"required",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean,attribute:"allow-custom-value"})],l.prototype,"allowCustomValue",void 0),(0,i.__decorate)([(0,s.MZ)()],l.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)()],l.prototype,"value",void 0),(0,i.__decorate)([(0,s.MZ)()],l.prototype,"helper",void 0),(0,i.__decorate)([(0,s.wk)()],l.prototype,"_opened",void 0),(0,i.__decorate)([(0,s.P)("ha-combo-box",!0)],l.prototype,"_comboBox",void 0),l=(0,i.__decorate)([(0,s.EM)("ha-entity-attribute-picker")],l);class u extends a.WF{render(){return a.qy`
      <ha-entity-attribute-picker
        .hass=${this.hass}
        .entityId=${this.selector.attribute?.entity_id||this.context?.filter_entity}
        .hideAttributes=${this.selector.attribute?.hide_attributes}
        .value=${this.value}
        .label=${this.label}
        .helper=${this.helper}
        .disabled=${this.disabled}
        .required=${this.required}
        allow-custom-value
      ></ha-entity-attribute-picker>
    `}updated(t){if(super.updated(t),!this.value||this.selector.attribute?.entity_id||!t.has("context"))return;const e=t.get("context");if(!this.context||!e||e.filter_entity===this.context.filter_entity)return;let o=!1;if(this.context.filter_entity){o=!(0,d.e)(this.context.filter_entity).some((t=>{const e=this.hass.states[t];return e&&this.value in e.attributes&&void 0!==e.attributes[this.value]}))}else o=void 0!==this.value;o&&(0,r.r)(this,"value-changed",{value:void 0})}constructor(...t){super(...t),this.disabled=!1,this.required=!0}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"selector",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"value",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"label",void 0),(0,i.__decorate)([(0,s.MZ)()],u.prototype,"helper",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"disabled",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"required",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],u.prototype,"context",void 0),u=(0,i.__decorate)([(0,s.EM)("ha-selector-attribute")],u)}};
//# sourceMappingURL=4948.6af06e6e69d52673.js.map