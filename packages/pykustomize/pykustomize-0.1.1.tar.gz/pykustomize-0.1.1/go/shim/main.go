// Copyright 2025 Vantage Compute
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

/*
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
	"sync"
	"unsafe"

	"sigs.k8s.io/kustomize/api/krusty"
	"sigs.k8s.io/kustomize/api/types"
	"sigs.k8s.io/kustomize/kyaml/filesys"
)

var (
	errMu          sync.Mutex
	lastErr        string
	versionCString *C.char
)

func init() {
	versionCString = C.CString("pykustomize-v0.1.0")
}

func setError(err error) C.int {
	errMu.Lock()
	defer errMu.Unlock()
	if err != nil {
		lastErr = err.Error()
		return -1
	}
	lastErr = ""
	return 0
}

//export pykustomize_last_error
func pykustomize_last_error() *C.char {
	errMu.Lock()
	defer errMu.Unlock()
	if lastErr == "" {
		return nil
	}
	return C.CString(lastErr)
}

//export pykustomize_free
func pykustomize_free(ptr unsafe.Pointer) {
	C.free(ptr)
}

//export pykustomize_version_string
func pykustomize_version_string() *C.char {
	return versionCString
}

//export pykustomize_version_number
func pykustomize_version_number() C.int {
	return 1 // Version 0.1.0
}

// BuildOptions represents the options for a kustomize build
type BuildOptions struct {
	// LoadRestrictions controls what files can be loaded
	// 0 = LoadRestrictionsRootOnly (default, secure)
	// 1 = LoadRestrictionsNone (allows loading from anywhere)
	LoadRestrictions int `json:"load_restrictions"`

	// Reorder controls the output order
	// "legacy" = fixed order for backwards compatibility
	// "none" = depth-first resource input order
	// "unspecified" = kustomize selects appropriate default
	Reorder string `json:"reorder"`

	// AddManagedbyLabel adds app.kubernetes.io/managed-by label
	AddManagedbyLabel bool `json:"add_managedby_label"`

	// EnablePlugins enables kustomize plugins
	EnablePlugins bool `json:"enable_plugins"`

	// EnableHelm enables helm chart inflation
	EnableHelm bool `json:"enable_helm"`

	// HelmCommand is the path to helm binary (if EnableHelm is true)
	HelmCommand string `json:"helm_command"`
}

//export pykustomize_build
func pykustomize_build(path *C.char, options_json *C.char, result **C.char) C.int {
	kustomizePath := C.GoString(path)

	// Parse options
	var opts BuildOptions
	optionsStr := C.GoString(options_json)
	if optionsStr != "" && optionsStr != "{}" {
		if err := json.Unmarshal([]byte(optionsStr), &opts); err != nil {
			return setError(fmt.Errorf("failed to parse options: %w", err))
		}
	}

	// Create krusty options
	kOpts := krusty.MakeDefaultOptions()

	// Configure load restrictions
	switch opts.LoadRestrictions {
	case 0:
		kOpts.LoadRestrictions = types.LoadRestrictionsRootOnly
	case 1:
		kOpts.LoadRestrictions = types.LoadRestrictionsNone
	}

	// Configure reorder
	switch opts.Reorder {
	case "legacy":
		kOpts.Reorder = krusty.ReorderOptionLegacy
	case "none":
		kOpts.Reorder = krusty.ReorderOptionNone
	default:
		kOpts.Reorder = krusty.ReorderOptionUnspecified
	}

	// Configure managed-by label
	kOpts.AddManagedbyLabel = opts.AddManagedbyLabel

	// Configure plugins
	if opts.EnablePlugins {
		kOpts.PluginConfig = types.EnabledPluginConfig(types.BploUseStaticallyLinked)
	}

	// Configure helm
	if opts.EnableHelm {
		if kOpts.PluginConfig == nil {
			kOpts.PluginConfig = types.EnabledPluginConfig(types.BploUseStaticallyLinked)
		}
		kOpts.PluginConfig.HelmConfig.Enabled = true
		if opts.HelmCommand != "" {
			kOpts.PluginConfig.HelmConfig.Command = opts.HelmCommand
		}
	}

	// Create kustomizer
	k := krusty.MakeKustomizer(kOpts)

	// Use the real filesystem
	fSys := filesys.MakeFsOnDisk()

	// Run kustomize build
	resMap, err := k.Run(fSys, kustomizePath)
	if err != nil {
		return setError(fmt.Errorf("kustomize build failed: %w", err))
	}

	// Convert result to YAML
	yaml, err := resMap.AsYaml()
	if err != nil {
		return setError(fmt.Errorf("failed to convert result to YAML: %w", err))
	}

	*result = C.CString(string(yaml))
	return 0
}

//export pykustomize_build_to_json
func pykustomize_build_to_json(path *C.char, options_json *C.char, result **C.char) C.int {
	kustomizePath := C.GoString(path)

	// Parse options
	var opts BuildOptions
	optionsStr := C.GoString(options_json)
	if optionsStr != "" && optionsStr != "{}" {
		if err := json.Unmarshal([]byte(optionsStr), &opts); err != nil {
			return setError(fmt.Errorf("failed to parse options: %w", err))
		}
	}

	// Create krusty options
	kOpts := krusty.MakeDefaultOptions()

	// Configure load restrictions
	switch opts.LoadRestrictions {
	case 0:
		kOpts.LoadRestrictions = types.LoadRestrictionsRootOnly
	case 1:
		kOpts.LoadRestrictions = types.LoadRestrictionsNone
	}

	// Configure reorder
	switch opts.Reorder {
	case "legacy":
		kOpts.Reorder = krusty.ReorderOptionLegacy
	case "none":
		kOpts.Reorder = krusty.ReorderOptionNone
	default:
		kOpts.Reorder = krusty.ReorderOptionUnspecified
	}

	// Configure managed-by label
	kOpts.AddManagedbyLabel = opts.AddManagedbyLabel

	// Configure plugins
	if opts.EnablePlugins {
		kOpts.PluginConfig = types.EnabledPluginConfig(types.BploUseStaticallyLinked)
	}

	// Configure helm
	if opts.EnableHelm {
		if kOpts.PluginConfig == nil {
			kOpts.PluginConfig = types.EnabledPluginConfig(types.BploUseStaticallyLinked)
		}
		kOpts.PluginConfig.HelmConfig.Enabled = true
		if opts.HelmCommand != "" {
			kOpts.PluginConfig.HelmConfig.Command = opts.HelmCommand
		}
	}

	// Create kustomizer
	k := krusty.MakeKustomizer(kOpts)

	// Use the real filesystem
	fSys := filesys.MakeFsOnDisk()

	// Run kustomize build
	resMap, err := k.Run(fSys, kustomizePath)
	if err != nil {
		return setError(fmt.Errorf("kustomize build failed: %w", err))
	}

	// Convert each resource to JSON and combine
	resources := resMap.Resources()
	jsonResources := make([]map[string]interface{}, 0, len(resources))

	for _, res := range resources {
		jsonBytes, err := res.MarshalJSON()
		if err != nil {
			return setError(fmt.Errorf("failed to marshal resource to JSON: %w", err))
		}
		var jsonMap map[string]interface{}
		if err := json.Unmarshal(jsonBytes, &jsonMap); err != nil {
			return setError(fmt.Errorf("failed to parse JSON: %w", err))
		}
		jsonResources = append(jsonResources, jsonMap)
	}

	// Create result object
	resultObj := map[string]interface{}{
		"resources": jsonResources,
		"count":     len(jsonResources),
	}

	resultBytes, err := json.Marshal(resultObj)
	if err != nil {
		return setError(fmt.Errorf("failed to serialize result: %w", err))
	}

	*result = C.CString(string(resultBytes))
	return 0
}

//export pykustomize_get_builtin_plugins
func pykustomize_get_builtin_plugins(result **C.char) C.int {
	plugins := krusty.GetBuiltinPluginNames()

	resultBytes, err := json.Marshal(plugins)
	if err != nil {
		return setError(fmt.Errorf("failed to serialize plugins: %w", err))
	}

	*result = C.CString(string(resultBytes))
	return 0
}

func main() {
	// Required for CGO shared library
}
