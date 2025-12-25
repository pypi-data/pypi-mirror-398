import matplotlib.pyplot as plt
import numpy as np
from astropy.convolution.utils import discretize_model
from tqdm import tqdm

class Plotter(object):   

    def plot_best(self, images, wavs, convolved_models, samples, fitter_keys, prior_handler):

        fig,axes=plt.subplots(3, images.shape[0], figsize=(images.shape[0],3))
        
        # Get median Nautilus parameters and transalte into median model parameters.
        param_dict = dict(zip(fitter_keys, np.median(samples, axis=0)))
        pars = prior_handler.revert(param_dict, wavs)

        for i in range(len(wavs)):
            convolved_models[i].parameters = pars[i]
            model = discretize_model(model=convolved_models[i], 
                                    x_range=[0,images[i].shape[1]], 
                                    y_range=[0,images[i].shape[0]], 
                                    mode='center')
            

            v = np.percentile(images[-1], 99.9)

            axes[0,i].imshow(images[i], vmax=v, vmin=-v)
            axes[0,i].set_axis_off()

            axes[1,i].imshow(model, vmax=v, vmin=-v)
            axes[1,i].set_axis_off()

            axes[2,i].imshow(images[i]-model, vmax=v, vmin=-v)
            axes[2,i].set_axis_off()


    def plot_median(self, images, wavs, convolved_models, samples, fitter_keys, prior_handler):

        fig,axes=plt.subplots(3, images.shape[0], figsize=(images.shape[0],3))
        

        models = np.zeros((samples.shape[0], *images.shape))

        print("Computing median model image...")
        for j in tqdm(range(samples.shape[0])):
            # Get median Nautilus parameters and transalte into median model parameters.
            param_dict = dict(zip(fitter_keys, samples[j]))
            pars = prior_handler.revert(param_dict, wavs)

            for k in range(len(wavs)):
                convolved_models[k].parameters = pars[k]
                model = discretize_model(model=convolved_models[k], 
                                        x_range=[0,images[k].shape[1]], 
                                        y_range=[0,images[k].shape[0]], 
                                        mode='center')
                models[j,k] = model


        median_models = np.median(models, axis=0)


        if len(wavs)==1:
            for i in range(len(wavs)):
                v = np.percentile(images[-1], 99.9)

                axes[0].imshow(images[i], vmax=v, vmin=-v)
                axes[0].set_axis_off()

                axes[1].imshow(median_models[i], vmax=v, vmin=-v)
                axes[1].set_axis_off()

                axes[2].imshow(images[i]-median_models[i], vmax=v, vmin=-v)
                axes[2].set_axis_off()

        else:
            for i in range(len(wavs)):

                v = np.percentile(images[-1], 99.9)

                axes[0,i].imshow(images[i], vmax=v, vmin=-v)
                axes[0,i].set_axis_off()

                axes[1,i].imshow(median_models[i], vmax=v, vmin=-v)
                axes[1,i].set_axis_off()

                axes[2,i].imshow(images[i]-median_models[i], vmax=v, vmin=-v)
                axes[2,i].set_axis_off()

