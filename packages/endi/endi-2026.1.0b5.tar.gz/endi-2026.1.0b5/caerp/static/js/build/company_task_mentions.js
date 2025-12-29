/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js":
/*!******************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js ***!
  \******************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _babel_runtime_helpers_esm_slicedToArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/esm/slicedToArray */ "./node_modules/@babel/runtime/helpers/esm/slicedToArray.js");
/* harmony import */ var _babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/helpers/esm/asyncToGenerator */ "./node_modules/@babel/runtime/helpers/esm/asyncToGenerator.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");
/* harmony import */ var _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @/stores/configurable_option */ "./src/stores/configurable_option.js");
/* harmony import */ var pinia__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! pinia */ "./node_modules/pinia/dist/pinia.mjs");
/* harmony import */ var _CompanyTaskMentionFormComponent_vue__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./CompanyTaskMentionFormComponent.vue */ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue");
/* harmony import */ var _layouts_FormModalLayout_vue__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! @/layouts/FormModalLayout.vue */ "./src/layouts/FormModalLayout.vue");
/* harmony import */ var _components_lists_Table_vue__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! @/components/lists/Table.vue */ "./src/components/lists/Table.vue");
/* harmony import */ var _columnDefs__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./columnDefs */ "./src/components/company/task_mentions/columnDefs.js");
/* harmony import */ var _components_Button_vue__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! @/components/Button.vue */ "./src/components/Button.vue");
/* harmony import */ var _components_Icon_vue__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! @/components/Icon.vue */ "./src/components/Icon.vue");














/**
 *
 * Charge les éléments
 * Charge le schéma de données
 *
 *
 * 1- Affichage d'une Liste
 * 2- Formulaire d'ajout / Modification d'un élément
 */

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({
  __name: 'CompanyTaskMentionComponent',
  props: {
    url: {
      type: String,
      required: true
    },
    formConfigUrl: {
      type: String,
      required: true
    }
  },
  setup: function setup(__props, _ref) {
    return (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().mark(function _callee2() {
      var _withAsyncContext2, _withAsyncContext3;
      var __expose, __temp, __restore, props, showForm, currentOptionId, listParams, dataStore, configStore, _storeToRefs, optionCollection, fetchData, _fetchData, addOption, editOption, onCancelAddEdit, onSaved, __returned__, _t, _t2, _t3, _t4, _t5, _t6, _t7, _t8, _t9, _t0, _t1, _t10, _t11, _t12, _t13, _t14, _t15, _t16;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().wrap(function (_context2) {
        while (1) switch (_context2.prev = _context2.next) {
          case 0:
            _fetchData = function _fetchData3() {
              _fetchData = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().mark(function _callee() {
                var promise, promise2;
                return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().wrap(function (_context) {
                  while (1) switch (_context.prev = _context.next) {
                    case 0:
                      promise = dataStore.setInitialValues(props.url);
                      promise2 = configStore.loadConfig();
                      _context.next = 1;
                      return Promise.all([promise, promise2]);
                    case 1:
                    case "end":
                      return _context.stop();
                  }
                }, _callee);
              }));
              return _fetchData.apply(this, arguments);
            };
            fetchData = function _fetchData2() {
              return _fetchData.apply(this, arguments);
            };
            __expose = _ref.expose;
            __expose();
            props = __props;
            showForm = (0,vue__WEBPACK_IMPORTED_MODULE_3__.ref)(false);
            currentOptionId = (0,vue__WEBPACK_IMPORTED_MODULE_3__.ref)(null);
            listParams = (0,vue__WEBPACK_IMPORTED_MODULE_3__.ref)({
              columnsDef: _columnDefs__WEBPACK_IMPORTED_MODULE_8__["default"],
              columns: _columnDefs__WEBPACK_IMPORTED_MODULE_8__["default"].map(function (column) {
                return column.name;
              })
            });
            dataStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionStore)();
            configStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionConfigStore)();
            configStore.setUrl(props.formConfigUrl);
            _storeToRefs = (0,pinia__WEBPACK_IMPORTED_MODULE_11__.storeToRefs)(dataStore), optionCollection = _storeToRefs.optionCollection;
            addOption = function addOption() {
              showForm.value = true;
            };
            editOption = function editOption(optionId) {
              showForm.value = true;
              currentOptionId.value = optionId;
            };
            onCancelAddEdit = function onCancelAddEdit() {
              showForm.value = false;
              currentOptionId.value = null;
            };
            onSaved = function onSaved(option) {
              console.log('Save option', option);
              showForm.value = false;
              currentOptionId.value = null;
            };
            _withAsyncContext2 = (0,vue__WEBPACK_IMPORTED_MODULE_3__.withAsyncContext)(function () {
              return fetchData();
            }), _withAsyncContext3 = (0,_babel_runtime_helpers_esm_slicedToArray__WEBPACK_IMPORTED_MODULE_0__["default"])(_withAsyncContext2, 2), __temp = _withAsyncContext3[0], __restore = _withAsyncContext3[1];
            _context2.next = 1;
            return __temp;
          case 1:
            __restore();
            _t = props;
            _t2 = showForm;
            _t3 = currentOptionId;
            _t4 = listParams;
            _t5 = dataStore;
            _t6 = configStore;
            _t7 = optionCollection;
            _t8 = fetchData;
            _t9 = addOption;
            _t0 = editOption;
            _t1 = onCancelAddEdit;
            _t10 = onSaved;
            _t11 = vue__WEBPACK_IMPORTED_MODULE_3__.ref;
            _t12 = _CompanyTaskMentionFormComponent_vue__WEBPACK_IMPORTED_MODULE_5__["default"];
            _t13 = _layouts_FormModalLayout_vue__WEBPACK_IMPORTED_MODULE_6__["default"];
            _t14 = _components_lists_Table_vue__WEBPACK_IMPORTED_MODULE_7__["default"];
            _t15 = _components_Button_vue__WEBPACK_IMPORTED_MODULE_9__["default"];
            _t16 = _components_Icon_vue__WEBPACK_IMPORTED_MODULE_10__["default"];
            __returned__ = {
              props: _t,
              showForm: _t2,
              currentOptionId: _t3,
              listParams: _t4,
              dataStore: _t5,
              configStore: _t6,
              optionCollection: _t7,
              fetchData: _t8,
              addOption: _t9,
              editOption: _t0,
              onCancelAddEdit: _t1,
              onSaved: _t10,
              ref: _t11,
              get useConfigurableOptionConfigStore() {
                return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionConfigStore;
              },
              get useConfigurableOptionStore() {
                return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionStore;
              },
              get storeToRefs() {
                return pinia__WEBPACK_IMPORTED_MODULE_11__.storeToRefs;
              },
              CompanyTaskMentionFormComponent: _t12,
              FormModalLayout: _t13,
              Table: _t14,
              get columnsDef() {
                return _columnDefs__WEBPACK_IMPORTED_MODULE_8__["default"];
              },
              Button: _t15,
              Icon: _t16
            };
            Object.defineProperty(__returned__, '__isScriptSetup', {
              enumerable: false,
              value: true
            });
            return _context2.abrupt("return", __returned__);
          case 2:
          case "end":
            return _context2.stop();
        }
      }, _callee2);
    }))();
  }
});

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js":
/*!*************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js ***!
  \*************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");
/* harmony import */ var vee_validate__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! vee-validate */ "./node_modules/vee-validate/dist/vee-validate.mjs");
/* harmony import */ var _helpers_form__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @/helpers/form */ "./src/helpers/form.js");
/* harmony import */ var _components_forms_Input_vue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @/components/forms/Input.vue */ "./src/components/forms/Input.vue");
/* harmony import */ var _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @/layouts/FormFlatLayout.vue */ "./src/layouts/FormFlatLayout.vue");
/* harmony import */ var _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @/stores/configurable_option */ "./src/stores/configurable_option.js");
/* harmony import */ var _components_forms_RichTextArea_vue__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! @/components/forms/RichTextArea.vue */ "./src/components/forms/RichTextArea.vue");







/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({
  __name: 'CompanyTaskMentionForm',
  props: {
    isEdit: {
      type: Boolean,
      "default": false
    },
    option: {
      type: Object,
      "default": null
    },
    layout: {
      type: Object,
      "default": _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_3__["default"]
    }
  },
  emits: ['saved', 'cancel', 'error'],
  setup: function setup(__props, _ref) {
    var __expose = _ref.expose,
      __emit = _ref.emit;
    __expose();
    var props = __props;
    var emit = __emit;
    var dataStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionStore)();
    var configStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionConfigStore)();

    // Configuration du schéma de formulaire et du Form vee-validate
    var jsonSchema = configStore.getSchema('default');
    var formSchema = (0,_helpers_form__WEBPACK_IMPORTED_MODULE_1__.buildYupSchema)(jsonSchema);
    var initialValues = (0,_helpers_form__WEBPACK_IMPORTED_MODULE_1__.getDefaults)(formSchema);
    Object.assign(initialValues, props.option);
    var _useForm = (0,vee_validate__WEBPACK_IMPORTED_MODULE_6__.useForm)({
        validationSchema: formSchema,
        initialValues: initialValues
      }),
      values = _useForm.values,
      handleSubmit = _useForm.handleSubmit,
      isSubmitting = _useForm.isSubmitting;

    /**
     * Fonction lancée lorsque la validation des données par vee-validate
     * est réussie/en erreur
     */
    var onSubmitSuccess = (0,_helpers_form__WEBPACK_IMPORTED_MODULE_1__.getSubmitModelCallback)(emit, dataStore.save);
    var onSubmitError = (0,_helpers_form__WEBPACK_IMPORTED_MODULE_1__.getSubmitErrorCallback)(emit);
    var onSubmit = handleSubmit(onSubmitSuccess, onSubmitError);
    var onCancel = function onCancel() {
      return emit('cancel');
    };
    var getData = function getData(fieldName) {
      return (0,_helpers_form__WEBPACK_IMPORTED_MODULE_1__.getFieldData)(formSchema, fieldName);
    };
    var __returned__ = {
      props: props,
      emit: emit,
      dataStore: dataStore,
      configStore: configStore,
      jsonSchema: jsonSchema,
      formSchema: formSchema,
      initialValues: initialValues,
      values: values,
      handleSubmit: handleSubmit,
      isSubmitting: isSubmitting,
      onSubmitSuccess: onSubmitSuccess,
      onSubmitError: onSubmitError,
      onSubmit: onSubmit,
      onCancel: onCancel,
      getData: getData,
      ref: vue__WEBPACK_IMPORTED_MODULE_0__.ref,
      computed: vue__WEBPACK_IMPORTED_MODULE_0__.computed,
      get useForm() {
        return vee_validate__WEBPACK_IMPORTED_MODULE_6__.useForm;
      },
      get buildYupSchema() {
        return _helpers_form__WEBPACK_IMPORTED_MODULE_1__.buildYupSchema;
      },
      get getFieldData() {
        return _helpers_form__WEBPACK_IMPORTED_MODULE_1__.getFieldData;
      },
      get getDefaults() {
        return _helpers_form__WEBPACK_IMPORTED_MODULE_1__.getDefaults;
      },
      get getSubmitErrorCallback() {
        return _helpers_form__WEBPACK_IMPORTED_MODULE_1__.getSubmitErrorCallback;
      },
      get getSubmitModelCallback() {
        return _helpers_form__WEBPACK_IMPORTED_MODULE_1__.getSubmitModelCallback;
      },
      Input: _components_forms_Input_vue__WEBPACK_IMPORTED_MODULE_2__["default"],
      FormFlatLayout: _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_3__["default"],
      get useConfigurableOptionConfigStore() {
        return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionConfigStore;
      },
      get useConfigurableOptionStore() {
        return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_4__.useConfigurableOptionStore;
      },
      RichTextArea: _components_forms_RichTextArea_vue__WEBPACK_IMPORTED_MODULE_5__["default"]
    };
    Object.defineProperty(__returned__, '__isScriptSetup', {
      enumerable: false,
      value: true
    });
    return __returned__;
  }
});

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js":
/*!**********************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js ***!
  \**********************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _babel_runtime_helpers_esm_slicedToArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/esm/slicedToArray */ "./node_modules/@babel/runtime/helpers/esm/slicedToArray.js");
/* harmony import */ var _babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/helpers/esm/asyncToGenerator */ "./node_modules/@babel/runtime/helpers/esm/asyncToGenerator.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");
/* harmony import */ var pinia__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! pinia */ "./node_modules/pinia/dist/pinia.mjs");
/* harmony import */ var _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @/layouts/FormFlatLayout.vue */ "./src/layouts/FormFlatLayout.vue");
/* harmony import */ var _CompanyTaskMentionForm_vue__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./CompanyTaskMentionForm.vue */ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue");
/* harmony import */ var _stores_configurable_option__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! @/stores/configurable_option */ "./src/stores/configurable_option.js");










// props attendu par le composant

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({
  __name: 'CompanyTaskMentionFormComponent',
  props: {
    optionId: {
      type: Number || null,
      "default": null
    },
    layout: {
      type: Object,
      "default": _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_4__["default"]
    }
  },
  emits: ['saved', 'cancel'],
  setup: function setup(__props, _ref) {
    return (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().mark(function _callee2() {
      var _withAsyncContext2, _withAsyncContext3;
      var __expose, __emit, __temp, __restore, props, emit, isEdit, loading, dataStore, configStore, preload, _storeToRefs, currentOption, onSaved, onCancel, __returned__, _t, _t2, _t3, _t4, _t5, _t6, _t7, _t8, _t9, _t0, _t1, _t10, _t11;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().wrap(function (_context2) {
        while (1) switch (_context2.prev = _context2.next) {
          case 0:
            onCancel = function _onCancel() {
              console.log('Cancel Option add/edit');
              emit('cancel');
            };
            onSaved = function _onSaved(option) {
              emit('saved', option);
            };
            __expose = _ref.expose, __emit = _ref.emit;
            __expose();
            props = __props;
            emit = __emit;
            isEdit = !!props.optionId;
            loading = (0,vue__WEBPACK_IMPORTED_MODULE_3__.ref)(true);
            dataStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_6__.useConfigurableOptionStore)();
            configStore = (0,_stores_configurable_option__WEBPACK_IMPORTED_MODULE_6__.useConfigurableOptionConfigStore)();
            preload = /*#__PURE__*/function () {
              var _ref2 = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_1__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().mark(function _callee() {
                var promises;
                return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_2___default().wrap(function (_context) {
                  while (1) switch (_context.prev = _context.next) {
                    case 0:
                      promises = [configStore.loadConfig()];
                      if (isEdit) {
                        promises.push(dataStore.loadOption(props.optionId));
                      } else {
                        promises.push(dataStore.setOptionId(null));
                      }
                      Promise.all(promises).then(function () {
                        return loading.value = false;
                      });
                    case 1:
                    case "end":
                      return _context.stop();
                  }
                }, _callee);
              }));
              return function preload() {
                return _ref2.apply(this, arguments);
              };
            }();
            _storeToRefs = (0,pinia__WEBPACK_IMPORTED_MODULE_7__.storeToRefs)(dataStore), currentOption = _storeToRefs.currentOption;
            ;
            _withAsyncContext2 = (0,vue__WEBPACK_IMPORTED_MODULE_3__.withAsyncContext)(function () {
              return preload();
            }), _withAsyncContext3 = (0,_babel_runtime_helpers_esm_slicedToArray__WEBPACK_IMPORTED_MODULE_0__["default"])(_withAsyncContext2, 2), __temp = _withAsyncContext3[0], __restore = _withAsyncContext3[1];
            _context2.next = 1;
            return __temp;
          case 1:
            __restore();
            _t = props;
            _t2 = emit;
            _t3 = isEdit;
            _t4 = loading;
            _t5 = dataStore;
            _t6 = configStore;
            _t7 = preload;
            _t8 = currentOption;
            _t9 = onSaved;
            _t0 = onCancel;
            _t1 = vue__WEBPACK_IMPORTED_MODULE_3__.ref;
            _t10 = _layouts_FormFlatLayout_vue__WEBPACK_IMPORTED_MODULE_4__["default"];
            _t11 = _CompanyTaskMentionForm_vue__WEBPACK_IMPORTED_MODULE_5__["default"];
            __returned__ = {
              props: _t,
              emit: _t2,
              isEdit: _t3,
              loading: _t4,
              dataStore: _t5,
              configStore: _t6,
              preload: _t7,
              currentOption: _t8,
              onSaved: _t9,
              onCancel: _t0,
              ref: _t1,
              get storeToRefs() {
                return pinia__WEBPACK_IMPORTED_MODULE_7__.storeToRefs;
              },
              FormFlatLayout: _t10,
              CompanyTaskMentionForm: _t11,
              get useConfigurableOptionConfigStore() {
                return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_6__.useConfigurableOptionConfigStore;
              },
              get useConfigurableOptionStore() {
                return _stores_configurable_option__WEBPACK_IMPORTED_MODULE_6__.useConfigurableOptionStore;
              }
            };
            Object.defineProperty(__returned__, '__isScriptSetup', {
              enumerable: false,
              value: true
            });
            return _context2.abrupt("return", __returned__);
          case 2:
          case "end":
            return _context2.stop();
        }
      }, _callee2);
    }))();
  }
});

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js":
/*!*************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js ***!
  \*************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");
/* harmony import */ var _helpers_context_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @/helpers/context.js */ "./src/helpers/context.js");
/* harmony import */ var _components_company_task_mentions_CompanyTaskMentionComponent_vue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @/components/company/task_mentions/CompanyTaskMentionComponent.vue */ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue");



/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({
  __name: 'App',
  setup: function setup(__props, _ref) {
    var __expose = _ref.expose;
    __expose();
    var options = (0,_helpers_context_js__WEBPACK_IMPORTED_MODULE_1__.collectOptions)();
    var redirectOnsave = function redirectOnsave() {
      window.location.replace('/companies/' + options.company_id);
    };
    var redirectOnCancel = function redirectOnCancel() {
      if (options['come_from']) {
        window.location.replace(options['come_from']);
      } else {
        window.location.href = options.context_url.replace('/api/v1/', '/');
      }
    };
    var __returned__ = {
      options: options,
      redirectOnsave: redirectOnsave,
      redirectOnCancel: redirectOnCancel,
      Suspense: vue__WEBPACK_IMPORTED_MODULE_0__.Suspense,
      get collectOptions() {
        return _helpers_context_js__WEBPACK_IMPORTED_MODULE_1__.collectOptions;
      },
      CompanyTaskMentionComponent: _components_company_task_mentions_CompanyTaskMentionComponent_vue__WEBPACK_IMPORTED_MODULE_2__["default"]
    };
    Object.defineProperty(__returned__, '__isScriptSetup', {
      enumerable: false,
      value: true
    });
    return __returned__;
  }
});

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497":
/*!***********************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497 ***!
  \***********************************************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* binding */ render)
/* harmony export */ });
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");

var _hoisted_1 = {
  "class": "limited_width width60"
};
var _hoisted_2 = {
  "class": "col_actions width_two"
};
var _hoisted_3 = {
  "class": "btn-group"
};
function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementBlock)("div", _hoisted_1, [_cache[0] || (_cache[0] = (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("div", {
    "class": "alert alert-info"
  }, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(" Vous pouvez configurer ici des mentions spécifiques qui vous seront proposées lorsque vous éditez des devis ou des factures."), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("br"), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(" Celles-ci apparaîtront alors dans les fichiers PDF sous la forme de cadres en dessous des prestations. ")], -1 /* CACHED */)), _cache[1] || (_cache[1] = (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("h2", null, "Liste des mentions", -1 /* CACHED */)), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Table"], {
    items: $setup.optionCollection,
    params: $setup.listParams
  }, {
    rowActions: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(function (_ref) {
      var item = _ref.item;
      return [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("td", _hoisted_2, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("div", _hoisted_3, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Button"], {
        "show-label": false,
        icon: "pen",
        label: "Modifier",
        title: "Ouvrir le formulaire de modification de l'élément",
        onClick: function onClick() {
          return $setup.editOption(item.id);
        }
      }, null, 8 /* PROPS */, ["onClick"]), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Button"], {
        "show-label": false,
        icon: "trash-alt",
        css: "negative",
        label: "Supprimer",
        title: "Supprimer l'élément",
        onClick: function onClick() {
          return $setup.dataStore.deleteOption(item.id);
        }
      }, null, 8 /* PROPS */, ["onClick"])])])];
    }),
    _: 1 /* STABLE */
  }, 8 /* PROPS */, ["items", "params"]), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Button"], {
    icon: "plus",
    label: "Ajouter un élément",
    onClick: $setup.addOption,
    "show-label": true
  }), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createCommentVNode)(" Formulaire d'ajout / Modification d'un élément "), $setup.showForm ? ((0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createBlock)($setup["CompanyTaskMentionFormComponent"], {
    key: 0,
    "option-id": $setup.currentOptionId,
    layout: $setup.FormModalLayout,
    onCancel: $setup.onCancelAddEdit,
    onSaved: $setup.onSaved
  }, null, 8 /* PROPS */, ["option-id"])) : (0,vue__WEBPACK_IMPORTED_MODULE_0__.createCommentVNode)("v-if", true)]);
}

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a":
/*!******************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a ***!
  \******************************************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* binding */ render)
/* harmony export */ });
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");

var _hoisted_1 = {
  "class": "deformFormFieldset"
};
var _hoisted_2 = {
  "class": "deformFormFieldset"
};
var _hoisted_3 = {
  "class": "btn-group"
};
var _hoisted_4 = ["disabled"];
function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createBlock)((0,vue__WEBPACK_IMPORTED_MODULE_0__.resolveDynamicComponent)($props.layout), {
    onSubmitForm: $setup.onSubmit,
    onClose: $setup.onCancel
  }, {
    title: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(function () {
      return [$props.isEdit ? ((0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementBlock)(vue__WEBPACK_IMPORTED_MODULE_0__.Fragment, {
        key: 0
      }, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(" Modifier une mention ")], 64 /* STABLE_FRAGMENT */)) : ((0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementBlock)(vue__WEBPACK_IMPORTED_MODULE_0__.Fragment, {
        key: 1
      }, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(" Ajouter une mention ")], 64 /* STABLE_FRAGMENT */))];
    }),
    fields: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(function () {
      return [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("fieldset", _hoisted_1, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Input"], (0,vue__WEBPACK_IMPORTED_MODULE_0__.normalizeProps)((0,vue__WEBPACK_IMPORTED_MODULE_0__.guardReactiveProps)($setup.getData('label'))), null, 16 /* FULL_PROPS */), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Input"], (0,vue__WEBPACK_IMPORTED_MODULE_0__.normalizeProps)((0,vue__WEBPACK_IMPORTED_MODULE_0__.guardReactiveProps)($setup.getData('help_text'))), null, 16 /* FULL_PROPS */)]), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("fieldset", _hoisted_2, [_cache[1] || (_cache[1] = (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("legend", null, "Sortie PDF", -1 /* CACHED */)), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["Input"], (0,vue__WEBPACK_IMPORTED_MODULE_0__.normalizeProps)((0,vue__WEBPACK_IMPORTED_MODULE_0__.guardReactiveProps)($setup.getData('title'))), null, 16 /* FULL_PROPS */), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)($setup["RichTextArea"], (0,vue__WEBPACK_IMPORTED_MODULE_0__.normalizeProps)((0,vue__WEBPACK_IMPORTED_MODULE_0__.guardReactiveProps)($setup.getData('full_text'))), null, 16 /* FULL_PROPS */)])];
    }),
    buttons: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(function () {
      return [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("div", _hoisted_3, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("button", {
        id: "deformsubmit",
        name: "submit",
        type: "submit",
        "class": "btn btn-primary",
        value: "submit",
        disabled: $setup.isSubmitting
      }, (0,vue__WEBPACK_IMPORTED_MODULE_0__.toDisplayString)($props.isEdit ? 'Modifier' : 'Valider'), 9 /* TEXT, PROPS */, _hoisted_4), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)("button", {
        id: "deformcancel",
        name: "cancel",
        type: "button",
        "class": "btn btn-default",
        onClick: _cache[0] || (_cache[0] = function () {
          return $setup.emit('cancel');
        })
      }, " Annuler ")])];
    }),
    _: 1 /* STABLE */
  }, 40 /* PROPS, NEED_HYDRATION */, ["onSubmitForm"]);
}

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a":
/*!***************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a ***!
  \***************************************************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* binding */ render)
/* harmony export */ });
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");

var _hoisted_1 = {
  key: 0
};
function render(_ctx, _cache, $props, $setup, $data, $options) {
  return $setup.loading ? ((0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementBlock)("div", _hoisted_1, "Chargement des informations")) : ((0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createBlock)($setup["CompanyTaskMentionForm"], {
    key: 1,
    option: $setup.currentOption,
    layout: $props.layout,
    onSaved: $setup.onSaved,
    onCancel: $setup.onCancel
  }, null, 8 /* PROPS */, ["option", "layout"]));
}

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9":
/*!******************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9 ***!
  \******************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* binding */ render)
/* harmony export */ });
/* harmony import */ var _babel_runtime_helpers_esm_toConsumableArray__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/esm/toConsumableArray */ "./node_modules/@babel/runtime/helpers/esm/toConsumableArray.js");
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");


function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (0,vue__WEBPACK_IMPORTED_MODULE_1__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_1__.createBlock)(vue__WEBPACK_IMPORTED_MODULE_1__.Suspense, null, {
    fallback: (0,vue__WEBPACK_IMPORTED_MODULE_1__.withCtx)(function () {
      return (0,_babel_runtime_helpers_esm_toConsumableArray__WEBPACK_IMPORTED_MODULE_0__["default"])(_cache[0] || (_cache[0] = [(0,vue__WEBPACK_IMPORTED_MODULE_1__.createTextVNode)(" Chargement... ", -1 /* CACHED */)]));
    }),
    "default": (0,vue__WEBPACK_IMPORTED_MODULE_1__.withCtx)(function () {
      return [(0,vue__WEBPACK_IMPORTED_MODULE_1__.createElementVNode)("div", null, [(0,vue__WEBPACK_IMPORTED_MODULE_1__.createVNode)($setup["CompanyTaskMentionComponent"], {
        url: $setup.options.context_url,
        "form-config-url": $setup.options.form_config_url,
        onOnSave: $setup.redirectOnsave,
        onOnCancel: $setup.redirectOnCancel
      }, null, 8 /* PROPS */, ["url", "form-config-url"])])];
    }),
    _: 1 /* STABLE */
  });
}

/***/ }),

/***/ "./src/components/company/task_mentions/columnDefs.js":
/*!************************************************************!*\
  !*** ./src/components/company/task_mentions/columnDefs.js ***!
  \************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _components_lists_cells_LabelCell_vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @/components/lists/cells/LabelCell.vue */ "./src/components/lists/cells/LabelCell.vue");
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");


var columnsDef = [{
  name: 'label',
  title: 'Libellé',
  cellComponent: (0,vue__WEBPACK_IMPORTED_MODULE_1__.markRaw)(_components_lists_cells_LabelCell_vue__WEBPACK_IMPORTED_MODULE_0__["default"]),
  css: 'col_text'
}, {
  name: 'title',
  title: 'Titre à afficher dans le PDF',
  cellComponent: (0,vue__WEBPACK_IMPORTED_MODULE_1__.markRaw)(_components_lists_cells_LabelCell_vue__WEBPACK_IMPORTED_MODULE_0__["default"]),
  css: 'col_text',
  componentOptions: {
    defaultValue: '-'
  }
}];
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (columnsDef);

/***/ }),

/***/ "./src/stores/configurable_option.js":
/*!*******************************************!*\
  !*** ./src/stores/configurable_option.js ***!
  \*******************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   useConfigurableOptionConfigStore: () => (/* binding */ useConfigurableOptionConfigStore),
/* harmony export */   useConfigurableOptionStore: () => (/* binding */ useConfigurableOptionStore)
/* harmony export */ });
/* harmony import */ var _babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @babel/runtime/helpers/esm/asyncToGenerator */ "./node_modules/@babel/runtime/helpers/esm/asyncToGenerator.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @babel/runtime/regenerator */ "./node_modules/@babel/runtime/regenerator/index.js");
/* harmony import */ var _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! vue */ "./node_modules/vue/dist/vue.runtime.esm-bundler.js");
/* harmony import */ var pinia__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! pinia */ "./node_modules/pinia/dist/pinia.mjs");
/* harmony import */ var _api_index__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @/api/index */ "./src/api/index.ts");
/* harmony import */ var _formConfig__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./formConfig */ "./src/stores/formConfig.js");






var useConfigurableOptionConfigStore = (0,_formConfig__WEBPACK_IMPORTED_MODULE_4__["default"])('configurable_option');
var useConfigurableOptionStore = (0,pinia__WEBPACK_IMPORTED_MODULE_5__.defineStore)('configurable_option', function () {
  var loading = (0,vue__WEBPACK_IMPORTED_MODULE_2__.ref)(true);
  var currentOptionId = (0,vue__WEBPACK_IMPORTED_MODULE_2__.ref)(null); // Option Id we're working on
  var currentOption = (0,vue__WEBPACK_IMPORTED_MODULE_2__.ref)({}); // The current Configurable Option object
  var optionCollection = (0,vue__WEBPACK_IMPORTED_MODULE_2__.ref)([]); // The current Configurable Option collection object
  var optionCollectionMeta = (0,vue__WEBPACK_IMPORTED_MODULE_2__.ref)({}); // Meta data about the collection
  function setInitialValues(_x) {
    return _setInitialValues.apply(this, arguments);
  }
  function _setInitialValues() {
    _setInitialValues = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee(collectionUrl) {
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context) {
        while (1) switch (_context.prev = _context.next) {
          case 0:
            _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option.setCollectionUrl(collectionUrl);
            loadOptionCollection();
          case 1:
          case "end":
            return _context.stop();
        }
      }, _callee);
    }));
    return _setInitialValues.apply(this, arguments);
  }
  function loadOptionCollection() {
    return _loadOptionCollection.apply(this, arguments);
  }
  function _loadOptionCollection() {
    _loadOptionCollection = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee2() {
      var loadOptions,
        result,
        _args2 = arguments;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context2) {
        while (1) switch (_context2.prev = _context2.next) {
          case 0:
            loadOptions = _args2.length > 0 && _args2[0] !== undefined ? _args2[0] : {};
            _context2.next = 1;
            return _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option.loadCollection(loadOptions);
          case 1:
            result = _context2.sent;
            optionCollection.value = result.items;
            optionCollectionMeta.value = result.metadata;
            loading.value = false;
          case 2:
          case "end":
            return _context2.stop();
        }
      }, _callee2);
    }));
    return _loadOptionCollection.apply(this, arguments);
  }
  function setOptionId(_x2) {
    return _setOptionId.apply(this, arguments);
  }
  function _setOptionId() {
    _setOptionId = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee3(optionId) {
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context3) {
        while (1) switch (_context3.prev = _context3.next) {
          case 0:
            currentOptionId.value = optionId;
            if (optionId === null) {
              currentOption.value = {};
            }
          case 1:
          case "end":
            return _context3.stop();
        }
      }, _callee3);
    }));
    return _setOptionId.apply(this, arguments);
  }
  function loadOption() {
    return _loadOption.apply(this, arguments);
  }
  function _loadOption() {
    _loadOption = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee4() {
      var optionId,
        option,
        _args4 = arguments;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context4) {
        while (1) switch (_context4.prev = _context4.next) {
          case 0:
            optionId = _args4.length > 0 && _args4[0] !== undefined ? _args4[0] : null;
            if (!optionId) optionId = currentOptionId.value;
            _context4.next = 1;
            return _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option.load(optionId);
          case 1:
            option = _context4.sent;
            currentOption.value = option;
            loading.value = false;
          case 2:
          case "end":
            return _context4.stop();
        }
      }, _callee4);
    }));
    return _loadOption.apply(this, arguments);
  }
  function createOption(_x3) {
    return _createOption.apply(this, arguments);
  }
  function _createOption() {
    _createOption = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee5(values) {
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context5) {
        while (1) switch (_context5.prev = _context5.next) {
          case 0:
            _context5.next = 1;
            return _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option.create(values);
          case 1:
            currentOption.value = _context5.sent;
            _context5.next = 2;
            return loadOptionCollection();
          case 2:
            return _context5.abrupt("return", currentOption.value);
          case 3:
          case "end":
            return _context5.stop();
        }
      }, _callee5);
    }));
    return _createOption.apply(this, arguments);
  }
  function updateOption(_x4) {
    return _updateOption.apply(this, arguments);
  }
  function _updateOption() {
    _updateOption = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee6(values) {
      var optionId,
        _args6 = arguments;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context6) {
        while (1) switch (_context6.prev = _context6.next) {
          case 0:
            optionId = _args6.length > 1 && _args6[1] !== undefined ? _args6[1] : null;
            _context6.next = 1;
            return _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option.update(values, optionId);
          case 1:
            currentOption.value = _context6.sent;
            _context6.next = 2;
            return loadOptionCollection();
          case 2:
            return _context6.abrupt("return", currentOption.value);
          case 3:
          case "end":
            return _context6.stop();
        }
      }, _callee6);
    }));
    return _updateOption.apply(this, arguments);
  }
  function save(_x5) {
    return _save.apply(this, arguments);
  }
  function _save() {
    _save = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee7(values) {
      var optionId,
        _args7 = arguments;
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context7) {
        while (1) switch (_context7.prev = _context7.next) {
          case 0:
            optionId = _args7.length > 1 && _args7[1] !== undefined ? _args7[1] : null;
            if (!(!values.id && !optionId)) {
              _context7.next = 1;
              break;
            }
            return _context7.abrupt("return", createOption(values));
          case 1:
            return _context7.abrupt("return", updateOption(values, optionId));
          case 2:
          case "end":
            return _context7.stop();
        }
      }, _callee7);
    }));
    return _save.apply(this, arguments);
  }
  function deleteOption(_x6) {
    return _deleteOption.apply(this, arguments);
  }
  function _deleteOption() {
    _deleteOption = (0,_babel_runtime_helpers_esm_asyncToGenerator__WEBPACK_IMPORTED_MODULE_0__["default"])(/*#__PURE__*/_babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().mark(function _callee8(optionId) {
      return _babel_runtime_regenerator__WEBPACK_IMPORTED_MODULE_1___default().wrap(function (_context8) {
        while (1) switch (_context8.prev = _context8.next) {
          case 0:
            _context8.next = 1;
            return _api_index__WEBPACK_IMPORTED_MODULE_3__["default"].configurable_option["delete"](optionId);
          case 1:
            _context8.next = 2;
            return loadOptionCollection();
          case 2:
          case "end":
            return _context8.stop();
        }
      }, _callee8);
    }));
    return _deleteOption.apply(this, arguments);
  }
  return {
    loading: loading,
    currentOptionId: currentOptionId,
    currentOption: currentOption,
    optionCollection: optionCollection,
    optionCollectionMeta: optionCollectionMeta,
    setInitialValues: setInitialValues,
    setOptionId: setOptionId,
    loadOption: loadOption,
    deleteOption: deleteOption,
    save: save
  };
});

/***/ }),

/***/ "./src/views/company/task_mentions/company_task_mentions.js":
/*!******************************************************************!*\
  !*** ./src/views/company/task_mentions/company_task_mentions.js ***!
  \******************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _helpers_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @/helpers/utils */ "./src/helpers/utils.js");
/* harmony import */ var _App_vue__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./App.vue */ "./src/views/company/task_mentions/App.vue");


var app = (0,_helpers_utils__WEBPACK_IMPORTED_MODULE_0__.startApp)(_App_vue__WEBPACK_IMPORTED_MODULE_1__["default"]);

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue":
/*!******************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionComponent.vue ***!
  \******************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _CompanyTaskMentionComponent_vue_vue_type_template_id_4864b497__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497 */ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497");
/* harmony import */ var _CompanyTaskMentionComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js */ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js");
/* harmony import */ var _node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../../node_modules/vue-loader/dist/exportHelper.js */ "./node_modules/vue-loader/dist/exportHelper.js");




;
const __exports__ = /*#__PURE__*/(0,_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__["default"])(_CompanyTaskMentionComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"], [['render',_CompanyTaskMentionComponent_vue_vue_type_template_id_4864b497__WEBPACK_IMPORTED_MODULE_0__.render],['__file',"src/components/company/task_mentions/CompanyTaskMentionComponent.vue"]])
/* hot reload */
if (false) {}


/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (__exports__);

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue":
/*!*************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionForm.vue ***!
  \*************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _CompanyTaskMentionForm_vue_vue_type_template_id_0b4a689a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a */ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a");
/* harmony import */ var _CompanyTaskMentionForm_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js */ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js");
/* harmony import */ var _node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../../node_modules/vue-loader/dist/exportHelper.js */ "./node_modules/vue-loader/dist/exportHelper.js");




;
const __exports__ = /*#__PURE__*/(0,_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__["default"])(_CompanyTaskMentionForm_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"], [['render',_CompanyTaskMentionForm_vue_vue_type_template_id_0b4a689a__WEBPACK_IMPORTED_MODULE_0__.render],['__file',"src/components/company/task_mentions/CompanyTaskMentionForm.vue"]])
/* hot reload */
if (false) {}


/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (__exports__);

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue":
/*!**********************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue ***!
  \**********************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _CompanyTaskMentionFormComponent_vue_vue_type_template_id_db1fb59a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a */ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a");
/* harmony import */ var _CompanyTaskMentionFormComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js */ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js");
/* harmony import */ var _node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../../node_modules/vue-loader/dist/exportHelper.js */ "./node_modules/vue-loader/dist/exportHelper.js");




;
const __exports__ = /*#__PURE__*/(0,_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__["default"])(_CompanyTaskMentionFormComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"], [['render',_CompanyTaskMentionFormComponent_vue_vue_type_template_id_db1fb59a__WEBPACK_IMPORTED_MODULE_0__.render],['__file',"src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue"]])
/* hot reload */
if (false) {}


/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (__exports__);

/***/ }),

/***/ "./src/views/company/task_mentions/App.vue":
/*!*************************************************!*\
  !*** ./src/views/company/task_mentions/App.vue ***!
  \*************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _App_vue_vue_type_template_id_76c013f9__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./App.vue?vue&type=template&id=76c013f9 */ "./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9");
/* harmony import */ var _App_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./App.vue?vue&type=script&setup=true&lang=js */ "./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js");
/* harmony import */ var _node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../../../node_modules/vue-loader/dist/exportHelper.js */ "./node_modules/vue-loader/dist/exportHelper.js");




;
const __exports__ = /*#__PURE__*/(0,_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__["default"])(_App_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_1__["default"], [['render',_App_vue_vue_type_template_id_76c013f9__WEBPACK_IMPORTED_MODULE_0__.render],['__file',"src/views/company/task_mentions/App.vue"]])
/* hot reload */
if (false) {}


/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (__exports__);

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js":
/*!*****************************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js ***!
  \*****************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"])
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=script&setup=true&lang=js");
 

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js":
/*!************************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js ***!
  \************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionForm_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"])
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionForm_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=script&setup=true&lang=js");
 

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js":
/*!*********************************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js ***!
  \*********************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionFormComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"])
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionFormComponent_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=script&setup=true&lang=js");
 

/***/ }),

/***/ "./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js":
/*!************************************************************************************!*\
  !*** ./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js ***!
  \************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_App_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__["default"])
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_App_vue_vue_type_script_setup_true_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./App.vue?vue&type=script&setup=true&lang=js */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=script&setup=true&lang=js");
 

/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497":
/*!************************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497 ***!
  \************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionComponent_vue_vue_type_template_id_4864b497__WEBPACK_IMPORTED_MODULE_0__.render)
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionComponent_vue_vue_type_template_id_4864b497__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497 */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionComponent.vue?vue&type=template&id=4864b497");


/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a":
/*!*******************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a ***!
  \*******************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionForm_vue_vue_type_template_id_0b4a689a__WEBPACK_IMPORTED_MODULE_0__.render)
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionForm_vue_vue_type_template_id_0b4a689a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionForm.vue?vue&type=template&id=0b4a689a");


/***/ }),

/***/ "./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a":
/*!****************************************************************************************************************!*\
  !*** ./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a ***!
  \****************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionFormComponent_vue_vue_type_template_id_db1fb59a__WEBPACK_IMPORTED_MODULE_0__.render)
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_CompanyTaskMentionFormComponent_vue_vue_type_template_id_db1fb59a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/components/company/task_mentions/CompanyTaskMentionFormComponent.vue?vue&type=template&id=db1fb59a");


/***/ }),

/***/ "./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9":
/*!*******************************************************************************!*\
  !*** ./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9 ***!
  \*******************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   render: () => (/* reexport safe */ _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_App_vue_vue_type_template_id_76c013f9__WEBPACK_IMPORTED_MODULE_0__.render)
/* harmony export */ });
/* harmony import */ var _node_modules_babel_loader_lib_index_js_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_2_node_modules_vue_loader_dist_index_js_ruleSet_1_rules_6_use_0_App_vue_vue_type_template_id_76c013f9__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js!../../../../node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./App.vue?vue&type=template&id=76c013f9 */ "./node_modules/babel-loader/lib/index.js!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[2]!./node_modules/vue-loader/dist/index.js??ruleSet[1].rules[6].use[0]!./src/views/company/task_mentions/App.vue?vue&type=template&id=76c013f9");


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			id: moduleId,
/******/ 			loaded: false,
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/chunk loaded */
/******/ 	(() => {
/******/ 		var deferred = [];
/******/ 		__webpack_require__.O = (result, chunkIds, fn, priority) => {
/******/ 			if(chunkIds) {
/******/ 				priority = priority || 0;
/******/ 				for(var i = deferred.length; i > 0 && deferred[i - 1][2] > priority; i--) deferred[i] = deferred[i - 1];
/******/ 				deferred[i] = [chunkIds, fn, priority];
/******/ 				return;
/******/ 			}
/******/ 			var notFulfilled = Infinity;
/******/ 			for (var i = 0; i < deferred.length; i++) {
/******/ 				var [chunkIds, fn, priority] = deferred[i];
/******/ 				var fulfilled = true;
/******/ 				for (var j = 0; j < chunkIds.length; j++) {
/******/ 					if ((priority & 1 === 0 || notFulfilled >= priority) && Object.keys(__webpack_require__.O).every((key) => (__webpack_require__.O[key](chunkIds[j])))) {
/******/ 						chunkIds.splice(j--, 1);
/******/ 					} else {
/******/ 						fulfilled = false;
/******/ 						if(priority < notFulfilled) notFulfilled = priority;
/******/ 					}
/******/ 				}
/******/ 				if(fulfilled) {
/******/ 					deferred.splice(i--, 1)
/******/ 					var r = fn();
/******/ 					if (r !== undefined) result = r;
/******/ 				}
/******/ 			}
/******/ 			return result;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/create fake namespace object */
/******/ 	(() => {
/******/ 		var getProto = Object.getPrototypeOf ? (obj) => (Object.getPrototypeOf(obj)) : (obj) => (obj.__proto__);
/******/ 		var leafPrototypes;
/******/ 		// create a fake namespace object
/******/ 		// mode & 1: value is a module id, require it
/******/ 		// mode & 2: merge all properties of value into the ns
/******/ 		// mode & 4: return value when already ns object
/******/ 		// mode & 16: return value when it's Promise-like
/******/ 		// mode & 8|1: behave like require
/******/ 		__webpack_require__.t = function(value, mode) {
/******/ 			if(mode & 1) value = this(value);
/******/ 			if(mode & 8) return value;
/******/ 			if(typeof value === 'object' && value) {
/******/ 				if((mode & 4) && value.__esModule) return value;
/******/ 				if((mode & 16) && typeof value.then === 'function') return value;
/******/ 			}
/******/ 			var ns = Object.create(null);
/******/ 			__webpack_require__.r(ns);
/******/ 			var def = {};
/******/ 			leafPrototypes = leafPrototypes || [null, getProto({}), getProto([]), getProto(getProto)];
/******/ 			for(var current = mode & 2 && value; typeof current == 'object' && !~leafPrototypes.indexOf(current); current = getProto(current)) {
/******/ 				Object.getOwnPropertyNames(current).forEach((key) => (def[key] = () => (value[key])));
/******/ 			}
/******/ 			def['default'] = () => (value);
/******/ 			__webpack_require__.d(ns, def);
/******/ 			return ns;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/ensure chunk */
/******/ 	(() => {
/******/ 		// The chunk loading function for additional chunks
/******/ 		// Since all referenced chunks are already included
/******/ 		// in this file, this function is empty here.
/******/ 		__webpack_require__.e = () => (Promise.resolve());
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/node module decorator */
/******/ 	(() => {
/******/ 		__webpack_require__.nmd = (module) => {
/******/ 			module.paths = [];
/******/ 			if (!module.children) module.children = [];
/******/ 			return module;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/publicPath */
/******/ 	(() => {
/******/ 		var scriptUrl;
/******/ 		if (__webpack_require__.g.importScripts) scriptUrl = __webpack_require__.g.location + "";
/******/ 		var document = __webpack_require__.g.document;
/******/ 		if (!scriptUrl && document) {
/******/ 			if (document.currentScript && document.currentScript.tagName.toUpperCase() === 'SCRIPT')
/******/ 				scriptUrl = document.currentScript.src;
/******/ 			if (!scriptUrl) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				if(scripts.length) {
/******/ 					var i = scripts.length - 1;
/******/ 					while (i > -1 && (!scriptUrl || !/^http(s?):/.test(scriptUrl))) scriptUrl = scripts[i--].src;
/******/ 				}
/******/ 			}
/******/ 		}
/******/ 		// When supporting browsers where an automatic publicPath is not supported you must specify an output.publicPath manually via configuration
/******/ 		// or pass an empty string ("") and set the __webpack_public_path__ variable from your code to use your own logic.
/******/ 		if (!scriptUrl) throw new Error("Automatic publicPath is not supported in this browser");
/******/ 		scriptUrl = scriptUrl.replace(/#.*$/, "").replace(/\?.*$/, "").replace(/\/[^\/]+$/, "/");
/******/ 		__webpack_require__.p = scriptUrl;
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		// no baseURI
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			"company_task_mentions": 0
/******/ 		};
/******/ 		
/******/ 		// no chunk on demand loading
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		__webpack_require__.O.j = (chunkId) => (installedChunks[chunkId] === 0);
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 			return __webpack_require__.O(result);
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = self["webpackChunkenDI"] = self["webpackChunkenDI"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/nonce */
/******/ 	(() => {
/******/ 		__webpack_require__.nc = undefined;
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module depends on other loaded chunks and execution need to be delayed
/******/ 	var __webpack_exports__ = __webpack_require__.O(undefined, ["vendor-vue"], () => (__webpack_require__("./src/views/company/task_mentions/company_task_mentions.js")))
/******/ 	__webpack_exports__ = __webpack_require__.O(__webpack_exports__);
/******/ 	
/******/ })()
;
//# sourceMappingURL=company_task_mentions.js.map