// Package mutate deals with AdmissionReview requests and responses, it takes in the request body and returns a readily converted JSON []byte that can be
// returned from a http Handler w/o needing to further convert or modify it, it also makes testing Mutate() kind of easy w/o need for a fake http server, etc.
package mutate

import (
	"encoding/json"
	"fmt"
	"log"

	v1beta1 "k8s.io/api/admission/v1beta1"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	epsagonImage = "epsagon/hello-python:latest"
)

type patchOperation struct {
	Op    string      `json:"op"`
	Path  string      `json:"path"`
	Value interface{} `json:"value,omitempty"`
}

// checkMutationRequired checks if a deployment should me mutated
func checkMutationRequired(deployment *appsv1.Deployment) (bool, int) {
	for containerIndex, container := range deployment.Spec.Template.Spec.Containers {
		if container.Image == epsagonImage {
			return true, containerIndex
		}
	}
	return false, 0
}

func addEnvVars(path string) []patchOperation {
	var patch []patchOperation
	patch = append(patch, patchOperation{
		Op:   "add",
		Path: path,
		Value: corev1.EnvVar{
			Name:  "EPSAGON_APP_NAME",
			Value: "TEST_APP_NAME",
		},
	})
	return patch
}

// Mutate a deployment
func mutate(deployment *appsv1.Deployment, containerIndex int) ([]patchOperation, error) {
	var patch []patchOperation
	basePath := fmt.Sprintf("/spec/template/spec/containers/%d", containerIndex)
	path := basePath + "/env"
	log.Printf("containerIndex = %d\n", containerIndex)
	log.Printf("container env: %v\n", deployment.Spec.Template.Spec.Containers[containerIndex].Env)
	if len(deployment.Spec.Template.Spec.Containers[containerIndex].Env) > 0 {
		path = path + "/-"
	}
	patch = append(patch, addEnvVars(path)...)
	return patch, nil
}

// Process mutates
func Process(body []byte, verbose bool) ([]byte, error) {
	if verbose {
		log.Printf("recv: %s\n", string(body)) // untested section
	}

	// unmarshal request into AdmissionReview struct
	admReview := v1beta1.AdmissionReview{}
	if err := json.Unmarshal(body, &admReview); err != nil {
		return nil, fmt.Errorf("unmarshaling request failed with %s", err)
	}

	var err error
	// var pod *corev1.Pod
	var deployment *appsv1.Deployment

	responseBody := []byte{}
	ar := admReview.Request
	resp := v1beta1.AdmissionResponse{}

	if ar != nil {

		// get the Pod object and unmarshal it into its struct, if we cannot, we might as well stop here
		if err := json.Unmarshal(ar.Object.Raw, &deployment); err != nil {
			return nil, fmt.Errorf("unable unmarshal deployment json object %v", err)
		}
		// set response options
		resp.Allowed = true
		resp.UID = ar.UID
		pT := v1beta1.PatchTypeJSONPatch
		resp.PatchType = &pT // it's annoying that this needs to be a pointer as you cannot give a pointer to a constant?

		// add some audit annotations, helpful to know why a object was modified, maybe (?)
		resp.AuditAnnotations = map[string]string{
			"mutateme": "yup it did it",
		}

		// Success, of course ;)
		resp.Result = &metav1.Status{
			Status: "Success",
		}
		var patch []patchOperation
		if shouldMutate, containerIndex := checkMutationRequired(deployment); shouldMutate {
			log.Printf("Mutating deployment\n")
			patch, err = mutate(deployment, containerIndex)
			if err != nil {
				resp.Result = &metav1.Status{
					Status: "Failure",
				}
				log.Printf("Error while mutating deployment: %v\n", err)
				patch = nil
			}
		}
		resp.Patch, err = json.Marshal(patch)

		admReview.Response = &resp
		// back into JSON so we can return the finished AdmissionReview w/ Response directly
		// w/o needing to convert things in the http handler
		responseBody, err = json.Marshal(admReview)
		if err != nil {
			return nil, err // untested section
		}
	}

	if verbose {
		log.Printf("resp: %s\n", string(responseBody)) // untested section
	}

	return responseBody, nil
}
