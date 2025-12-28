"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1364"],{28175:function(e,a,t){t.a(e,(async function(e,i){try{t.r(a),t.d(a,{HaFormInteger:function(){return y}});var s=t(44734),h=t(56038),d=t(69683),l=t(6454),r=(t(78170),t(52675),t(89463),t(28706),t(62826)),n=t(96196),o=t(77845),u=t(92542),c=t(60808),v=(t(70524),t(56768),t(78740),e([c]));c=(v.then?(await v)():v)[0];var p,f,m,_,g,b=e=>e,y=function(e){function a(){var e;(0,s.A)(this,a);for(var t=arguments.length,i=new Array(t),h=0;h<t;h++)i[h]=arguments[h];return(e=(0,d.A)(this,a,[].concat(i))).disabled=!1,e}return(0,l.A)(a,e),(0,h.A)(a,[{key:"focus",value:function(){this._input&&this._input.focus()}},{key:"render",value:function(){var e,a;return void 0!==this.schema.valueMin&&void 0!==this.schema.valueMax&&this.schema.valueMax-this.schema.valueMin<256?(0,n.qy)(p||(p=b`
        <div>
          ${0}
          <div class="flex">
            ${0}
            <ha-slider
              labeled
              .value=${0}
              .min=${0}
              .max=${0}
              .disabled=${0}
              @change=${0}
            ></ha-slider>
          </div>
          ${0}
        </div>
      `),this.label,this.schema.required?"":(0,n.qy)(f||(f=b`
                  <ha-checkbox
                    @change=${0}
                    .checked=${0}
                    .disabled=${0}
                  ></ha-checkbox>
                `),this._handleCheckboxChange,void 0!==this.data,this.disabled),this._value,this.schema.valueMin,this.schema.valueMax,this.disabled||void 0===this.data&&!this.schema.required,this._valueChanged,this.helper?(0,n.qy)(m||(m=b`<ha-input-helper-text .disabled=${0}
                >${0}</ha-input-helper-text
              >`),this.disabled,this.helper):""):(0,n.qy)(_||(_=b`
      <ha-textfield
        type="number"
        inputMode="numeric"
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
    `),this.label,this.helper,void 0!==this.data?this.data:"",this.disabled,this.schema.required,this.schema.required,null===(e=this.schema.description)||void 0===e?void 0:e.suffix,this.schema.required?null===(a=this.localize)||void 0===a?void 0:a.call(this,"ui.common.error_required"):void 0,this._valueChanged)}},{key:"updated",value:function(e){e.has("schema")&&this.toggleAttribute("own-margin",!("valueMin"in this.schema&&"valueMax"in this.schema||!this.schema.required))}},{key:"_value",get:function(){var e,a;return void 0!==this.data?this.data:this.schema.required?void 0!==(null===(e=this.schema.description)||void 0===e?void 0:e.suggested_value)&&null!==(null===(a=this.schema.description)||void 0===a?void 0:a.suggested_value)||this.schema.default||this.schema.valueMin||0:this.schema.valueMin||0}},{key:"_handleCheckboxChange",value:function(e){var a;if(e.target.checked)for(var t=0,i=[this._lastValue,null===(s=this.schema.description)||void 0===s?void 0:s.suggested_value,this.schema.default,0];t<i.length;t++){var s,h=i[t];if(void 0!==h){a=h;break}}else this._lastValue=this.data;(0,u.r)(this,"value-changed",{value:a})}},{key:"_valueChanged",value:function(e){var a,t=e.target,i=t.value;if(""!==i&&(a=parseInt(String(i))),this.data!==a)(0,u.r)(this,"value-changed",{value:a});else{var s=void 0===a?"":String(a);t.value!==s&&(t.value=s)}}}])}(n.WF);y.styles=(0,n.AH)(g||(g=b`
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
  `)),(0,r.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"localize",void 0),(0,r.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"schema",void 0),(0,r.__decorate)([(0,o.MZ)({attribute:!1})],y.prototype,"data",void 0),(0,r.__decorate)([(0,o.MZ)()],y.prototype,"label",void 0),(0,r.__decorate)([(0,o.MZ)()],y.prototype,"helper",void 0),(0,r.__decorate)([(0,o.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,r.__decorate)([(0,o.P)("ha-textfield ha-slider")],y.prototype,"_input",void 0),y=(0,r.__decorate)([(0,o.EM)("ha-form-integer")],y),i()}catch(x){i(x)}}))}}]);
//# sourceMappingURL=1364.926359ce0c0aa46d.js.map