"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5306"],{29261:function(e,t,i){var a,o,r,d,s,l,n,h,u,c=i(44734),p=i(56038),m=i(69683),b=i(6454),y=(i(28706),i(2892),i(26099),i(38781),i(68156),i(62826)),v=i(96196),f=i(77845),_=i(32288),g=i(92542),x=i(55124),$=(i(60733),i(56768),i(56565),i(69869),i(78740),e=>e),M=function(e){function t(){var e;(0,c.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,m.A)(this,t,[].concat(a))).autoValidate=!1,e.required=!1,e.format=12,e.disabled=!1,e.days=0,e.hours=0,e.minutes=0,e.seconds=0,e.milliseconds=0,e.dayLabel="",e.hourLabel="",e.minLabel="",e.secLabel="",e.millisecLabel="",e.enableSecond=!1,e.enableMillisecond=!1,e.enableDay=!1,e.noHoursLimit=!1,e.amPm="AM",e}return(0,b.A)(t,e),(0,p.A)(t,[{key:"render",value:function(){return(0,v.qy)(a||(a=$`
      ${0}
      <div class="time-input-wrap-wrap">
        <div class="time-input-wrap">
          ${0}

          <ha-textfield
            id="hour"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            name="hours"
            @change=${0}
            @focusin=${0}
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max=${0}
            min="0"
            .disabled=${0}
            suffix=":"
            class="hasSuffix"
          >
          </ha-textfield>
          <ha-textfield
            id="min"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            @change=${0}
            @focusin=${0}
            name="minutes"
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max="59"
            min="0"
            .disabled=${0}
            .suffix=${0}
            class=${0}
          >
          </ha-textfield>
          ${0}
          ${0}
          ${0}
        </div>

        ${0}
      </div>
      ${0}
    `),this.label?(0,v.qy)(o||(o=$`<label>${0}${0}</label>`),this.label,this.required?" *":""):v.s6,this.enableDay?(0,v.qy)(r||(r=$`
                <ha-textfield
                  id="day"
                  type="number"
                  inputmode="numeric"
                  .value=${0}
                  .label=${0}
                  name="days"
                  @change=${0}
                  @focusin=${0}
                  no-spinner
                  .required=${0}
                  .autoValidate=${0}
                  min="0"
                  .disabled=${0}
                  suffix=":"
                  class="hasSuffix"
                >
                </ha-textfield>
              `),this.days.toFixed(),this.dayLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):v.s6,this.hours.toFixed(),this.hourLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,(0,_.J)(this._hourMax),this.disabled,this._formatValue(this.minutes),this.minLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableSecond?":":"",this.enableSecond?"has-suffix":"",this.enableSecond?(0,v.qy)(d||(d=$`<ha-textfield
                id="sec"
                type="number"
                inputmode="numeric"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="seconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="2"
                max="59"
                min="0"
                .disabled=${0}
                .suffix=${0}
                class=${0}
              >
              </ha-textfield>`),this._formatValue(this.seconds),this.secLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableMillisecond?":":"",this.enableMillisecond?"has-suffix":""):v.s6,this.enableMillisecond?(0,v.qy)(s||(s=$`<ha-textfield
                id="millisec"
                type="number"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="milliseconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="3"
                max="999"
                min="0"
                .disabled=${0}
              >
              </ha-textfield>`),this._formatValue(this.milliseconds,3),this.millisecLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):v.s6,!this.clearable||this.required||this.disabled?v.s6:(0,v.qy)(l||(l=$`<ha-icon-button
                label="clear"
                @click=${0}
                .path=${0}
              ></ha-icon-button>`),this._clearValue,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"),24===this.format?v.s6:(0,v.qy)(n||(n=$`<ha-select
              .required=${0}
              .value=${0}
              .disabled=${0}
              name="amPm"
              naturalMenuWidth
              fixedMenuPosition
              @selected=${0}
              @closed=${0}
            >
              <ha-list-item value="AM">AM</ha-list-item>
              <ha-list-item value="PM">PM</ha-list-item>
            </ha-select>`),this.required,this.amPm,this.disabled,this._valueChanged,x.d),this.helper?(0,v.qy)(h||(h=$`<ha-input-helper-text .disabled=${0}
            >${0}</ha-input-helper-text
          >`),this.disabled,this.helper):v.s6)}},{key:"_clearValue",value:function(){(0,g.r)(this,"value-changed")}},{key:"_valueChanged",value:function(e){var t=e.currentTarget;this[t.name]="amPm"===t.name?t.value:Number(t.value);var i={hours:this.hours,minutes:this.minutes,seconds:this.seconds,milliseconds:this.milliseconds};this.enableDay&&(i.days=this.days),12===this.format&&(i.amPm=this.amPm),(0,g.r)(this,"value-changed",{value:i})}},{key:"_onFocus",value:function(e){e.currentTarget.select()}},{key:"_formatValue",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;return e.toString().padStart(t,"0")}},{key:"_hourMax",get:function(){if(!this.noHoursLimit)return 12===this.format?12:23}}])}(v.WF);M.styles=(0,v.AH)(u||(u=$`
    :host([clearable]) {
      position: relative;
    }
    .time-input-wrap-wrap {
      display: flex;
    }
    .time-input-wrap {
      display: flex;
      flex: var(--time-input-flex, unset);
      border-radius: var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--ha-border-radius-square) var(--ha-border-radius-square);
      overflow: hidden;
      position: relative;
      direction: ltr;
      padding-right: 3px;
    }
    ha-textfield {
      width: 60px;
      flex-grow: 1;
      text-align: center;
      --mdc-shape-small: 0;
      --text-field-appearance: none;
      --text-field-padding: 0 4px;
      --text-field-suffix-padding-left: 2px;
      --text-field-suffix-padding-right: 0;
      --text-field-text-align: center;
    }
    ha-textfield.hasSuffix {
      --text-field-padding: 0 0 0 4px;
    }
    ha-textfield:first-child {
      --text-field-border-top-left-radius: var(--mdc-shape-medium);
    }
    ha-textfield:last-child {
      --text-field-border-top-right-radius: var(--mdc-shape-medium);
    }
    ha-select {
      --mdc-shape-small: 0;
      width: 85px;
    }
    :host([clearable]) .mdc-select__anchor {
      padding-inline-end: var(--select-selected-text-padding-end, 12px);
    }
    ha-icon-button {
      position: relative;
      --mdc-icon-button-size: 36px;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
      direction: var(--direction);
      display: flex;
      align-items: center;
      background-color: var(--mdc-text-field-fill-color, whitesmoke);
      border-bottom-style: solid;
      border-bottom-width: 1px;
    }
    label {
      -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
      -webkit-font-smoothing: var(--ha-font-smoothing);
      font-family: var(
        --mdc-typography-body2-font-family,
        var(--mdc-typography-font-family, var(--ha-font-family-body))
      );
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      line-height: var(
        --mdc-typography-body2-line-height,
        var(--ha-line-height-condensed)
      );
      font-weight: var(
        --mdc-typography-body2-font-weight,
        var(--ha-font-weight-normal)
      );
      letter-spacing: var(
        --mdc-typography-body2-letter-spacing,
        0.0178571429em
      );
      text-decoration: var(--mdc-typography-body2-text-decoration, inherit);
      text-transform: var(--mdc-typography-body2-text-transform, inherit);
      color: var(--mdc-theme-text-primary-on-background, rgba(0, 0, 0, 0.87));
      padding-left: 4px;
      padding-inline-start: 4px;
      padding-inline-end: initial;
    }
    ha-input-helper-text {
      padding-top: 8px;
      line-height: var(--ha-line-height-condensed);
    }
  `)),(0,y.__decorate)([(0,f.MZ)()],M.prototype,"label",void 0),(0,y.__decorate)([(0,f.MZ)()],M.prototype,"helper",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"auto-validate",type:Boolean})],M.prototype,"autoValidate",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"required",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"format",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"days",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"hours",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"minutes",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"seconds",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"milliseconds",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"day-label"})],M.prototype,"dayLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"hour-label"})],M.prototype,"hourLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"min-label"})],M.prototype,"minLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"sec-label"})],M.prototype,"secLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"ms-label"})],M.prototype,"millisecLabel",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-second",type:Boolean})],M.prototype,"enableSecond",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-millisecond",type:Boolean})],M.prototype,"enableMillisecond",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-day",type:Boolean})],M.prototype,"enableDay",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"no-hours-limit",type:Boolean})],M.prototype,"noHoursLimit",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:!1})],M.prototype,"amPm",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean,reflect:!0})],M.prototype,"clearable",void 0),M=(0,y.__decorate)([(0,f.EM)("ha-base-time-input")],M)},33464:function(e,t,i){var a,o=i(44734),r=i(56038),d=i(69683),s=i(6454),l=(i(28706),i(2892),i(62826)),n=i(96196),h=i(77845),u=i(92542),c=(i(29261),e=>e),p=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(a))).required=!1,e.enableMillisecond=!1,e.enableDay=!1,e.disabled=!1,e}return(0,s.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,n.qy)(a||(a=c`
      <ha-base-time-input
        .label=${0}
        .helper=${0}
        .required=${0}
        .clearable=${0}
        .autoValidate=${0}
        .disabled=${0}
        errorMessage="Required"
        enable-second
        .enableMillisecond=${0}
        .enableDay=${0}
        format="24"
        .days=${0}
        .hours=${0}
        .minutes=${0}
        .seconds=${0}
        .milliseconds=${0}
        @value-changed=${0}
        no-hours-limit
        day-label="dd"
        hour-label="hh"
        min-label="mm"
        sec-label="ss"
        ms-label="ms"
      ></ha-base-time-input>
    `),this.label,this.helper,this.required,!this.required&&void 0!==this.data,this.required,this.disabled,this.enableMillisecond,this.enableDay,this._days,this._hours,this._minutes,this._seconds,this._milliseconds,this._durationChanged)}},{key:"_days",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.days?Number(this.data.days):this.required||this.data?0:NaN}},{key:"_hours",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.hours?Number(this.data.hours):this.required||this.data?0:NaN}},{key:"_minutes",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.minutes?Number(this.data.minutes):this.required||this.data?0:NaN}},{key:"_seconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.seconds?Number(this.data.seconds):this.required||this.data?0:NaN}},{key:"_milliseconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.milliseconds?Number(this.data.milliseconds):this.required||this.data?0:NaN}},{key:"_durationChanged",value:function(e){e.stopPropagation();var t,i=e.detail.value?Object.assign({},e.detail.value):void 0;i&&(i.hours||(i.hours=0),i.minutes||(i.minutes=0),i.seconds||(i.seconds=0),"days"in i&&(i.days||(i.days=0)),"milliseconds"in i&&(i.milliseconds||(i.milliseconds=0)),this.enableMillisecond||i.milliseconds?i.milliseconds>999&&(i.seconds+=Math.floor(i.milliseconds/1e3),i.milliseconds%=1e3):delete i.milliseconds,i.seconds>59&&(i.minutes+=Math.floor(i.seconds/60),i.seconds%=60),i.minutes>59&&(i.hours+=Math.floor(i.minutes/60),i.minutes%=60),this.enableDay&&i.hours>24&&(i.days=(null!==(t=i.days)&&void 0!==t?t:0)+Math.floor(i.hours/24),i.hours%=24));(0,u.r)(this,"value-changed",{value:i})}}])}(n.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],p.prototype,"data",void 0),(0,l.__decorate)([(0,h.MZ)()],p.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)()],p.prototype,"helper",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],p.prototype,"required",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:"enable-millisecond",type:Boolean})],p.prototype,"enableMillisecond",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:"enable-day",type:Boolean})],p.prototype,"enableDay",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,h.EM)("ha-duration-input")],p)},53089:function(e,t,i){i.r(t),i.d(t,{HaTimeDuration:function(){return c}});var a,o=i(44734),r=i(56038),d=i(69683),s=i(6454),l=(i(28706),i(62826)),n=i(96196),h=i(77845),u=(i(33464),e=>e),c=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(a))).disabled=!1,e.required=!0,e}return(0,s.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e,t;return(0,n.qy)(a||(a=u`
      <ha-duration-input
        .label=${0}
        .helper=${0}
        .data=${0}
        .disabled=${0}
        .required=${0}
        .enableDay=${0}
        .enableMillisecond=${0}
      ></ha-duration-input>
    `),this.label,this.helper,this.value,this.disabled,this.required,null===(e=this.selector.duration)||void 0===e?void 0:e.enable_day,null===(t=this.selector.duration)||void 0===t?void 0:t.enable_millisecond)}}])}(n.WF);(0,l.__decorate)([(0,h.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],c.prototype,"selector",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],c.prototype,"value",void 0),(0,l.__decorate)([(0,h.MZ)()],c.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)()],c.prototype,"helper",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],c.prototype,"required",void 0),c=(0,l.__decorate)([(0,h.EM)("ha-selector-duration")],c)}}]);
//# sourceMappingURL=5306.56fc666ae635e4d4.js.map