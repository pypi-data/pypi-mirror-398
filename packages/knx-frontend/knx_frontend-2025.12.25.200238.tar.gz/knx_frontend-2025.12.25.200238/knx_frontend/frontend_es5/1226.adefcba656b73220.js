"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1226"],{92726:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(31432),o=a(44734),r=a(56038),u=a(69683),n=a(6454),s=(a(28706),a(2008),a(74423),a(23792),a(62062),a(44114),a(18111),a(22489),a(61701),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953),a(62826)),l=a(96196),d=a(77845),h=a(55376),c=a(92542),v=a(55179),p=t([v]);v=(p.then?(await p)():p)[0];var _,y=t=>t,b=function(t){function e(){var t;(0,o.A)(this,e);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(t=(0,u.A)(this,e,[].concat(i))).autofocus=!1,t.disabled=!1,t.required=!1,t._opened=!1,t}return(0,n.A)(e,t),(0,r.A)(e,[{key:"shouldUpdate",value:function(t){return!(!t.has("_opened")&&this._opened)}},{key:"updated",value:function(t){if(t.has("_opened")&&this._opened||t.has("entityId")||t.has("attribute")){var e,a=(this.entityId?(0,h.e)(this.entityId):[]).map((t=>{var e=this.hass.states[t];return e?Object.keys(e.attributes).filter((t=>{var e;return!(null!==(e=this.hideAttributes)&&void 0!==e&&e.includes(t))})).map((t=>({value:t,label:this.hass.formatEntityAttributeName(e,t)}))):[]})),o=[],r=new Set,u=(0,i.A)(a);try{for(u.s();!(e=u.n()).done;){var n,s=e.value,l=(0,i.A)(s);try{for(l.s();!(n=l.n()).done;){var d=n.value;r.has(d.value)||(r.add(d.value),o.push(d))}}catch(c){l.e(c)}finally{l.f()}}}catch(c){u.e(c)}finally{u.f()}this._comboBox.filteredItems=o}}},{key:"render",value:function(){var t;return this.hass?(0,l.qy)(_||(_=y`
      <ha-combo-box
        .hass=${0}
        .value=${0}
        .autofocus=${0}
        .label=${0}
        .disabled=${0}
        .required=${0}
        .helper=${0}
        .allowCustomValue=${0}
        item-id-path="value"
        item-value-path="value"
        item-label-path="label"
        @opened-changed=${0}
        @value-changed=${0}
      >
      </ha-combo-box>
    `),this.hass,this.value,this.autofocus,null!==(t=this.label)&&void 0!==t?t:this.hass.localize("ui.components.entity.entity-attribute-picker.attribute"),this.disabled||!this.entityId,this.required,this.helper,this.allowCustomValue,this._openedChanged,this._valueChanged):l.s6}},{key:"_value",get:function(){return this.value||""}},{key:"_openedChanged",value:function(t){this._opened=t.detail.value}},{key:"_valueChanged",value:function(t){t.stopPropagation();var e=t.detail.value;e!==this._value&&this._setValue(e)}},{key:"_setValue",value:function(t){this.value=t,setTimeout((()=>{(0,c.r)(this,"value-changed",{value:t}),(0,c.r)(this,"change")}),0)}}])}(l.WF);(0,s.__decorate)([(0,d.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],b.prototype,"entityId",void 0),(0,s.__decorate)([(0,d.MZ)({type:Array,attribute:"hide-attributes"})],b.prototype,"hideAttributes",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],b.prototype,"autofocus",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],b.prototype,"required",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"allow-custom-value"})],b.prototype,"allowCustomValue",void 0),(0,s.__decorate)([(0,d.MZ)()],b.prototype,"label",void 0),(0,s.__decorate)([(0,d.MZ)()],b.prototype,"value",void 0),(0,s.__decorate)([(0,d.MZ)()],b.prototype,"helper",void 0),(0,s.__decorate)([(0,d.wk)()],b.prototype,"_opened",void 0),(0,s.__decorate)([(0,d.P)("ha-combo-box",!0)],b.prototype,"_comboBox",void 0),b=(0,s.__decorate)([(0,d.EM)("ha-entity-attribute-picker")],b),e()}catch(f){e(f)}}))},73889:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{HaSelectorAttribute:function(){return f}});var o=a(44734),r=a(56038),u=a(69683),n=a(6454),s=a(25460),l=(a(28706),a(18111),a(13579),a(26099),a(62826)),d=a(96196),h=a(77845),c=a(92542),v=a(92726),p=a(55376),_=t([v]);v=(_.then?(await _)():_)[0];var y,b=t=>t,f=function(t){function e(){var t;(0,o.A)(this,e);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(t=(0,u.A)(this,e,[].concat(i))).disabled=!1,t.required=!0,t}return(0,n.A)(e,t),(0,r.A)(e,[{key:"render",value:function(){var t,e,a;return(0,d.qy)(y||(y=b`
      <ha-entity-attribute-picker
        .hass=${0}
        .entityId=${0}
        .hideAttributes=${0}
        .value=${0}
        .label=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        allow-custom-value
      ></ha-entity-attribute-picker>
    `),this.hass,(null===(t=this.selector.attribute)||void 0===t?void 0:t.entity_id)||(null===(e=this.context)||void 0===e?void 0:e.filter_entity),null===(a=this.selector.attribute)||void 0===a?void 0:a.hide_attributes,this.value,this.label,this.helper,this.disabled,this.required)}},{key:"updated",value:function(t){var a;if((0,s.A)(e,"updated",this,3)([t]),this.value&&(null===(a=this.selector.attribute)||void 0===a||!a.entity_id)&&t.has("context")){var i=t.get("context");if(this.context&&i&&i.filter_entity!==this.context.filter_entity){var o=!1;if(this.context.filter_entity)o=!(0,p.e)(this.context.filter_entity).some((t=>{var e=this.hass.states[t];return e&&this.value in e.attributes&&void 0!==e.attributes[this.value]}));else o=void 0!==this.value;o&&(0,c.r)(this,"value-changed",{value:void 0})}}}}])}(d.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],f.prototype,"selector",void 0),(0,l.__decorate)([(0,h.MZ)()],f.prototype,"value",void 0),(0,l.__decorate)([(0,h.MZ)()],f.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)()],f.prototype,"helper",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],f.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],f.prototype,"required",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],f.prototype,"context",void 0),f=(0,l.__decorate)([(0,h.EM)("ha-selector-attribute")],f),i()}catch(k){i(k)}}))}}]);
//# sourceMappingURL=1226.adefcba656b73220.js.map