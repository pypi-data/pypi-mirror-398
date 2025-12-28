"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8389"],{33092:function(e,t,i){i.r(t),i.d(t,{HaFormString:function(){return y}});var s,a,o,r,n=i(44734),d=i(56038),h=i(69683),l=i(6454),u=(i(78170),i(52675),i(89463),i(28706),i(74423),i(26099),i(62826)),c=i(96196),p=i(77845),m=i(92542),v=(i(60733),i(78740),e=>e),f=["password","secret","token"],y=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,s=new Array(i),a=0;a<i;a++)s[a]=arguments[a];return(e=(0,h.A)(this,t,[].concat(s))).localizeBaseKey="ui.components.selectors.text",e.disabled=!1,e.unmaskedPassword=!1,e}return(0,l.A)(t,e),(0,d.A)(t,[{key:"focus",value:function(){this._input&&this._input.focus()}},{key:"render",value:function(){var e,t;return(0,c.qy)(s||(s=v`
      <ha-textfield
        .type=${0}
        .label=${0}
        .value=${0}
        .helper=${0}
        helperPersistent
        .disabled=${0}
        .required=${0}
        .autoValidate=${0}
        .name=${0}
        .autofocus=${0}
        .autocomplete=${0}
        .suffix=${0}
        .validationMessage=${0}
        @input=${0}
        @change=${0}
      ></ha-textfield>
      ${0}
    `),this.isPassword?this.unmaskedPassword?"text":"password":this.stringType,this.label,this.data||"",this.helper,this.disabled,this.schema.required,this.schema.required,this.schema.name,this.schema.autofocus,this.schema.autocomplete,this.isPassword?(0,c.qy)(a||(a=v`<div style="width: 24px"></div>`)):null===(e=this.schema.description)||void 0===e?void 0:e.suffix,this.schema.required?null===(t=this.localize)||void 0===t?void 0:t.call(this,"ui.common.error_required"):void 0,this._valueChanged,this._valueChanged,this.renderIcon())}},{key:"renderIcon",value:function(){var e;return this.isPassword?(0,c.qy)(o||(o=v`
      <ha-icon-button
        .label=${0}
        @click=${0}
        .path=${0}
      ></ha-icon-button>
    `),null===(e=this.localize)||void 0===e?void 0:e.call(this,`${this.localizeBaseKey}.${this.unmaskedPassword?"hide_password":"show_password"}`),this.toggleUnmaskedPassword,this.unmaskedPassword?"M11.83,9L15,12.16C15,12.11 15,12.05 15,12A3,3 0 0,0 12,9C11.94,9 11.89,9 11.83,9M7.53,9.8L9.08,11.35C9.03,11.56 9,11.77 9,12A3,3 0 0,0 12,15C12.22,15 12.44,14.97 12.65,14.92L14.2,16.47C13.53,16.8 12.79,17 12,17A5,5 0 0,1 7,12C7,11.21 7.2,10.47 7.53,9.8M2,4.27L4.28,6.55L4.73,7C3.08,8.3 1.78,10 1,12C2.73,16.39 7,19.5 12,19.5C13.55,19.5 15.03,19.2 16.38,18.66L16.81,19.08L19.73,22L21,20.73L3.27,3M12,7A5,5 0 0,1 17,12C17,12.64 16.87,13.26 16.64,13.82L19.57,16.75C21.07,15.5 22.27,13.86 23,12C21.27,7.61 17,4.5 12,4.5C10.6,4.5 9.26,4.75 8,5.2L10.17,7.35C10.74,7.13 11.35,7 12,7Z":"M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z"):c.s6}},{key:"updated",value:function(e){e.has("schema")&&this.toggleAttribute("own-margin",!!this.schema.required)}},{key:"toggleUnmaskedPassword",value:function(){this.unmaskedPassword=!this.unmaskedPassword}},{key:"_valueChanged",value:function(e){var t=e.target.value;this.data!==t&&(""!==t||this.schema.required||(t=void 0),(0,m.r)(this,"value-changed",{value:t}))}},{key:"stringType",get:function(){if(this.schema.format){if(["email","url"].includes(this.schema.format))return this.schema.format;if("fqdnurl"===this.schema.format)return"url"}return"text"}},{key:"isPassword",get:function(){return f.some((e=>this.schema.name.includes(e)))}}])}(c.WF);y.styles=(0,c.AH)(r||(r=v`
    :host {
      display: block;
      position: relative;
    }
    :host([own-margin]) {
      margin-bottom: 5px;
    }
    ha-textfield {
      display: block;
    }
    ha-icon-button {
      position: absolute;
      top: 8px;
      right: 8px;
      inset-inline-start: initial;
      inset-inline-end: 8px;
      --mdc-icon-button-size: 40px;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
      direction: var(--direction);
    }
  `)),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],y.prototype,"localize",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],y.prototype,"localizeBaseKey",void 0),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],y.prototype,"schema",void 0),(0,u.__decorate)([(0,p.MZ)()],y.prototype,"data",void 0),(0,u.__decorate)([(0,p.MZ)()],y.prototype,"label",void 0),(0,u.__decorate)([(0,p.MZ)()],y.prototype,"helper",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,u.__decorate)([(0,p.wk)()],y.prototype,"unmaskedPassword",void 0),(0,u.__decorate)([(0,p.P)("ha-textfield")],y.prototype,"_input",void 0),y=(0,u.__decorate)([(0,p.EM)("ha-form-string")],y)}}]);
//# sourceMappingURL=8389.d02957337087ae2f.js.map