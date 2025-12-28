"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["812"],{5863:function(e,t,a){a.r(t),a.d(t,{HaFormFloat:function(){return v}});var i,o,r=a(44734),d=a(56038),n=a(69683),s=a(6454),l=(a(78170),a(52675),a(89463),a(28706),a(27495),a(25440),a(62826)),u=a(96196),h=a(77845),c=a(92542),p=(a(78740),e=>e),v=function(e){function t(){var e;(0,r.A)(this,t);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(i))).disabled=!1,e}return(0,s.A)(t,e),(0,d.A)(t,[{key:"focus",value:function(){this._input&&this._input.focus()}},{key:"render",value:function(){var e,t;return(0,u.qy)(i||(i=p`
      <ha-textfield
        type="number"
        inputMode="decimal"
        step="any"
        .label=${0}
        .helper=${0}
        helperPersistent
        .value=${0}
        .disabled=${0}
        .required=${0}
        .autoValidate=${0}
        .suffix=${0}
        .validationMessage=${0}
        @input=${0}
      ></ha-textfield>
    `),this.label,this.helper,void 0!==this.data?this.data:"",this.disabled,this.schema.required,this.schema.required,null===(e=this.schema.description)||void 0===e?void 0:e.suffix,this.schema.required?null===(t=this.localize)||void 0===t?void 0:t.call(this,"ui.common.error_required"):void 0,this._valueChanged)}},{key:"updated",value:function(e){e.has("schema")&&this.toggleAttribute("own-margin",!!this.schema.required)}},{key:"_valueChanged",value:function(e){var t,a=e.target.value.replace(",",".");a.endsWith(".")||"-"!==a&&(""!==a&&(t=parseFloat(a),isNaN(t)&&(t=void 0)),this.data!==t&&(0,c.r)(this,"value-changed",{value:t}))}}])}(u.WF);v.styles=(0,u.AH)(o||(o=p`
    :host([own-margin]) {
      margin-bottom: 5px;
    }
    ha-textfield {
      display: block;
    }
  `)),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"localize",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"schema",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"data",void 0),(0,l.__decorate)([(0,h.MZ)()],v.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)()],v.prototype,"helper",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],v.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.P)("ha-textfield")],v.prototype,"_input",void 0),v=(0,l.__decorate)([(0,h.EM)("ha-form-float")],v)}}]);
//# sourceMappingURL=812.579fdbb5d3435de2.js.map