import * as vscode from 'vscode';
import { extensionConfigurationService } from '../utils/extension_configuration_service';
import { FeatureFlag } from './constants';

// Published so the UI toggle only appears when the flag is explicitly set to a
// boolean. When the flag is unset (`null`) the old UI is shown without a toggle.
const CONFIGURED_CONTEXT_KEY = 'gitlab:duoAgentPlatformNewUIConfigured';

const updateContext = () => {
  const value =
    extensionConfigurationService.getConfiguration().featureFlags[FeatureFlag.DuoAgentPlatformNext];
  return vscode.commands.executeCommand(
    'setContext',
    CONFIGURED_CONTEXT_KEY,
    typeof value === 'boolean',
  );
};

// Reuses the same change flow the local feature flag service uses to publish
// the flag's view-driving context key, so the toggle's visibility and the
// active view switch atomically on a live flag change.
export const setupDuoAgentPlatformNextContext = async (): Promise<vscode.Disposable> => {
  await updateContext();

  return extensionConfigurationService.onChange(updateContext);
};
